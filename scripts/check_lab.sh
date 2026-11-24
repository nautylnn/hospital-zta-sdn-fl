#!/usr/bin/env bash
set -euo pipefail

ENV_PROFILE="${1:-member1_local}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
INVENTORY="${REPO_ROOT}/infra/ansible/inventories/${ENV_PROFILE}/hosts.ini"
export ANSIBLE_CONFIG="${REPO_ROOT}/infra/ansible/ansible.cfg"

if [[ ! -f "${INVENTORY}" ]]; then
  echo "[ERROR] Khong tim thay inventory: ${INVENTORY}"
  exit 1
fi

echo "=== 1. KIEM TRA ICMP PING TOI CAC NODE TRONG PROFILE: ${ENV_PROFILE} ==="
HOSTS=$(awk '
  /^\[/{in_section=($0 ~ /^\[(core_switches|access_switches|hospital_servers)\]/); next}
  in_section && !/^#/ && /ansible_host=/ {
    for (i=1; i<=NF; i++) {
      if ($i ~ /^ansible_host=/) {
        split($i, a, "=");
        print $1 ":" a[2];
      }
    }
  }
' "${INVENTORY}")

for entry in ${HOSTS}; do
  name="${entry%%:*}"
  ip="${entry##*:}"
  if ping -c 2 -W 1 "${ip}" >/dev/null 2>&1; then
    echo "  [OK]   ${name} (${ip})"
  else
    echo "  [FAIL] ${name} (${ip})"
  fi
done

echo ""
echo "=== 2. KIEM TRA KET NOI SSH & ENABLE TREN CISCO SWITCHES ==="
ansible all_switches -i "${INVENTORY}" -m cisco.ios.ios_command -a "commands='show version | include uptime'"

echo ""
echo "=== 3. KIEM TRA TRANG THAI HSRP TREN CORE SWITCHES ==="
ansible core_switches -i "${INVENTORY}" -m cisco.ios.ios_command -a "commands='show standby brief'"
