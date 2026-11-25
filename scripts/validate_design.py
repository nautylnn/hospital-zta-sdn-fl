#!/usr/bin/env python3
"""Offline SSOT, Security ACL, Inventory, JSON Contract, and Hygiene Validator."""

from __future__ import annotations

import ipaddress
import json
import sys
from pathlib import Path
from typing import Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_PERSONAL_PREFIX = "/mnt/c/" + "Uni/"


class ValidationFailure(Exception):
    """Raised when a design or policy invariant fails."""


def load_yaml(path: Path) -> object:
    """Load and parse a YAML file."""
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def check_yaml_files() -> str:
    """Parse network_spec.yml, all inventory group_vars, and all playbooks."""
    targets = [REPO_ROOT / "design" / "network_spec.yml"]
    targets.extend(sorted((REPO_ROOT / "infra" / "ansible" / "inventories").glob("*/group_vars/all.yml")))
    targets.extend(sorted((REPO_ROOT / "infra" / "ansible" / "playbooks").glob("*.yml")))
    targets.append(REPO_ROOT / "infra" / "ansible" / "requirements.yml")

    for path in targets:
        if not path.is_file():
            raise ValidationFailure(f"Missing expected YAML file: {path.relative_to(REPO_ROOT)}")
        data = load_yaml(path)
        if data is None:
            raise ValidationFailure(f"Empty YAML file: {path.relative_to(REPO_ROOT)}")
    return f"Parsed {len(targets)} YAML files cleanly"


def check_ssot_invariants() -> str:
    """Verify VLAN counts, trunk exclusions, HSRP uniqueness, access VLANs, and DC server IPs."""
    spec = load_yaml(REPO_ROOT / "design" / "network_spec.yml")
    assert isinstance(spec, dict)

    vlans = spec.get("hospital_vlans", [])
    if len(vlans) != 12:
        raise ValidationFailure(f"Expected 12 hospital_vlans, found {len(vlans)}")

    vlan_ids = [v["vlan_id"] for v in vlans]
    vlan_names = [v["name"] for v in vlans]
    if len(set(vlan_ids)) != len(vlan_ids) or len(set(vlan_names)) != len(vlan_names):
        raise ValidationFailure("Duplicate vlan_id or name detected in hospital_vlans")

    vlan_id_set = set(vlan_ids)
    gs = spec["global_settings"]
    dmz_vlan = gs["dmz_vlan_id"]
    oob_vlan = gs["oob_vlan_id"]
    if dmz_vlan not in vlan_id_set or oob_vlan not in vlan_id_set:
        raise ValidationFailure("dmz_vlan_id or oob_vlan_id missing from hospital_vlans")

    trunk_vlans = {int(x.strip()) for x in gs["trunk_allowed_vlans"].split(",")}
    if oob_vlan in trunk_vlans or dmz_vlan in trunk_vlans:
        raise ValidationFailure("OOB (999) or DMZ (210) must NOT appear in trunk_allowed_vlans")

    svis = spec["core_svi_hsrp"]
    acls = spec["security_acls"]
    seen_groups, seen_vips, seen_c1, seen_c2 = set(), set(), set(), set()
    for svi in svis:
        vid = svi["vlan_id"]
        if vid not in vlan_id_set or vid not in trunk_vlans:
            raise ValidationFailure(f"SVI VLAN {vid} missing from hospital_vlans or trunk_allowed_vlans")
        for key, bucket in [
            ("hsrp_group", seen_groups),
            ("vip", seen_vips),
            ("core1_ip", seen_c1),
            ("core2_ip", seen_c2),
        ]:
            val = svi[key]
            if val in bucket:
                raise ValidationFailure(f"Duplicate {key}={val} across core_svi_hsrp")
            bucket.add(val)
        if "acl_in" in svi and svi["acl_in"] not in acls:
            raise ValidationFailure(f"SVI VLAN {vid} references undefined ACL {svi['acl_in']}")

    for sw_name, profile in spec["switch_port_profiles"].items():
        for port in profile.get("access", []):
            if port["vlan"] not in vlan_id_set:
                raise ValidationFailure(f"{sw_name} port {port['port']} uses undefined VLAN {port['vlan']}")

    dc_net = ipaddress.IPv4Network("192.168.200.0/24")
    reserved = {ipaddress.IPv4Address(f"192.168.200.{i}") for i in (1, 2, 3)}
    seen_dc_ips = set()
    for srv_name, srv in spec["dc_servers"].items():
        addr = ipaddress.IPv4Address(srv["ip"])
        if addr not in dc_net or addr in reserved or addr in seen_dc_ips:
            raise ValidationFailure(f"Invalid or colliding DC server IP for {srv_name}: {addr}")
        seen_dc_ips.add(addr)

    return f"12 VLANs, {len(svis)} SVIs/HSRP, {len(seen_dc_ips)} DC IPs verified"


def check_security_acls() -> str:
    """Enforce Zero-Trust ACL invariants (no Guest leak, no IoMT default-allow, VTY OOB lock)."""
    spec = load_yaml(REPO_ROOT / "design" / "network_spec.yml")
    assert isinstance(spec, dict)
    acls = spec["security_acls"]

    guest_rules = acls.get("GUEST", [])
    for subnet in ("192.168.220.0", "192.168.230.0"):
        expected = f"deny ip {subnet} 0.0.0.255 192.168.0.0 0.0.255.255"
        if not any(expected in r for r in guest_rules):
            raise ValidationFailure(f"GUEST ACL must deny all IP traffic from {subnet} to 192.168.0.0/16")
    if not any("{{ oob_network }}" in r and r.startswith("deny ip") for r in guest_rules):
        raise ValidationFailure("GUEST ACL must deny access to oob_network")

    iomt_rules = acls.get("IOMT_ZTA_BASELINE", [])
    if any("permit ip any any" in r for r in iomt_rules):
        raise ValidationFailure("IOMT_ZTA_BASELINE must NOT contain 'permit ip any any'")
    if not iomt_rules or not iomt_rules[-1].startswith("deny ip any any"):
        raise ValidationFailure("IOMT_ZTA_BASELINE must end with default-deny ('deny ip any any')")
    if not any("deny ip 192.168.180.0 0.0.0.255 192.168.0.0 0.0.255.255" in r for r in iomt_rules):
        raise ValidationFailure("IOMT_ZTA_BASELINE must block lateral movement to 192.168.0.0/16")

    clinical_rules = acls.get("CLINICAL_PROTECT_OOB", [])
    if not any("{{ oob_network }}" in r and r.startswith("deny ip") for r in clinical_rules):
        raise ValidationFailure("CLINICAL_PROTECT_OOB must deny access to oob_network")

    vty = spec.get("vty_access_list", {})
    if vty.get("name") != "OOB_VTY_ONLY":
        raise ValidationFailure("vty_access_list.name must be OOB_VTY_ONLY")
    vty_lines = vty.get("lines", [])
    if not any("{{ oob_network }}" in ln and ln.startswith("permit ") for ln in vty_lines):
        raise ValidationFailure("OOB_VTY_ONLY must permit oob_network")
    if not vty_lines or not vty_lines[-1].startswith("deny any"):
        raise ValidationFailure("OOB_VTY_ONLY must end with 'deny any'")

    return "GUEST, IOMT_ZTA_BASELINE, CLINICAL_PROTECT_OOB, OOB_VTY_ONLY verified"


def check_inventories() -> str:
    """Verify all 4 environment profiles contain hosts.ini and required group_vars."""
    profiles = ("member1_local", "member2_local", "lead_lite", "cloud_full")
    required_vars = {"oob_network", "oob_wildcard", "server_data_interface", "ios_user", "server_user"}
    inv_root = REPO_ROOT / "infra" / "ansible" / "inventories"

    for profile in profiles:
        hosts_file = inv_root / profile / "hosts.ini"
        vars_file = inv_root / profile / "group_vars" / "all.yml"
        if not hosts_file.is_file() or not vars_file.is_file():
            raise ValidationFailure(f"Profile {profile} missing hosts.ini or group_vars/all.yml")
        hosts_text = hosts_file.read_text(encoding="utf-8")
        for section in ("[core_switches]", "[access_switches]", "[all_switches:children]", "[hospital_servers]"):
            if section not in hosts_text:
                raise ValidationFailure(f"{profile}/hosts.ini missing section {section}")
        vars_data = load_yaml(vars_file)
        assert isinstance(vars_data, dict)
        missing = required_vars - set(vars_data.keys())
        if missing:
            raise ValidationFailure(f"{profile}/group_vars/all.yml missing keys: {sorted(missing)}")

    return f"Verified {len(profiles)} inventory profiles ({', '.join(profiles)})"


def check_json_contracts() -> str:
    """Validate JSON Schema syntax and required properties in contracts/."""
    expected = {
        "alert_schema.json": {"alert_id", "timestamp", "edge_id", "switch_dpid", "src_mac", "src_ip", "attack_type", "confidence"},
        "enforcement_schema.json": {"decision", "switch_dpid", "match_mac", "match_ip", "ttl_seconds", "priority", "reason", "alert_id"},
    }
    for filename, req_fields in expected.items():
        path = REPO_ROOT / "contracts" / filename
        if not path.is_file():
            raise ValidationFailure(f"Missing contract file: contracts/{filename}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if "$schema" not in data or "required" not in data or "properties" not in data:
            raise ValidationFailure(f"contracts/{filename} is not a complete JSON Schema")
        missing = req_fields - set(data["required"])
        if missing:
            raise ValidationFailure(f"contracts/{filename} missing required fields: {sorted(missing)}")

    return "Validated alert_schema.json and enforcement_schema.json"


def check_path_hygiene() -> str:
    """Ensure no hardcoded personal Windows/WSL drive paths exist anywhere in the repo."""
    scanned = 0
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scanned += 1
        if FORBIDDEN_PERSONAL_PREFIX in text:
            raise ValidationFailure(f"Hardcoded personal path found in {path.relative_to(REPO_ROOT)}")

    return f"Scanned {scanned} text files with zero hardcoded personal paths"


def main() -> int:
    """Run all validation suites and print a summary table."""
    checks: list[tuple[str, Callable[[], str]]] = [
        ("YAML Syntax", check_yaml_files),
        ("SSOT Invariants", check_ssot_invariants),
        ("Zero-Trust ACLs", check_security_acls),
        ("Inventories (4 Profiles)", check_inventories),
        ("JSON Contracts", check_json_contracts),
        ("Path Hygiene", check_path_hygiene),
    ]

    failures = 0
    print("=" * 78)
    print("HOSPITAL ZTA-SDN-FL :: OFFLINE DESIGN & IAC VALIDATION")
    print("=" * 78)
    for name, fn in checks:
        try:
            detail = fn()
            print(f"[PASS] {name:<25} | {detail}")
        except (ValidationFailure, yaml.YAMLError, json.JSONDecodeError, KeyError, AssertionError) as exc:
            failures += 1
            print(f"[FAIL] {name:<25} | {exc}")
    print("=" * 78)

    if failures:
        print(f"RESULT: FAILED ({failures} check(s) failed)")
        return 1
    print("RESULT: ALL CHECKS PASSED (0 failures)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
