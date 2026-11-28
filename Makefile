# ==============================================================================
# Hospital ZTA + SDN + Federated Learning IDS (Open-Source IaC)
# Usage:
#   make validate
#   make check-lab ENV=member1_local
#   make deploy-step1 ENV=member1_local
#   make deploy-hospital-apps ENV=member1_local
#   make verify-hospital-apps ENV=member1_local
#   make verify-step1 ENV=lead_lite
# ==============================================================================

ENV ?= member1_local
PYTHON ?= python3

ANSIBLE_CFG := infra/ansible/ansible.cfg
INVENTORY := infra/ansible/inventories/$(ENV)/hosts.ini
PLAYBOOK_DIR := infra/ansible/playbooks

.DEFAULT_GOAL := help

.PHONY: help validate check-lab reset-cisco deploy-core deploy-servers deploy-step1 verify-step1 deploy-hospital-apps verify-hospital-apps syntax-check

help: ## Hien thi danh sach lenh ho tro
	@echo "Hospital ZTA-SDN-FL Pipeline (ENV=$(ENV))"
	@echo "Profiles hop le: member1_local | member2_local | lead_lite | cloud_full"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  make %-22s %s\n", $$1, $$2}'

validate: ## Kiem tra YAML, logic VLAN/HSRP/ACL, JSON contracts (chay offline)
	$(PYTHON) scripts/validate_design.py

check-lab: ## Kiem tra Ping, SSH & trang thai HSRP cua lab (ENV=...)
	bash scripts/check_lab.sh $(ENV)

syntax-check: ## Kiem tra cu phap Ansible toan bo playbook
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook -i $(INVENTORY) --syntax-check \
		$(PLAYBOOK_DIR)/00_reset_cisco.yml \
		$(PLAYBOOK_DIR)/01_core_cisco.yml \
		$(PLAYBOOK_DIR)/02_servers_base.yml \
		$(PLAYBOOK_DIR)/03_hospital_apps.yml \
		$(PLAYBOOK_DIR)/98_verify_hospital_apps.yml \
		$(PLAYBOOK_DIR)/99_verify_step1.yml

reset-cisco: ## Dua 7 Cisco Switch ve flash:bootstrap.cfg (serial: 2)
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook -i $(INVENTORY) $(PLAYBOOK_DIR)/00_reset_cisco.yml

deploy-core: ## Trien khai L2/L3 VLAN, HSRP, STP, ACL & VTY hardening len Cisco Switches
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook -i $(INVENTORY) $(PLAYBOOK_DIR)/01_core_cisco.yml

deploy-servers: ## Tu dong cai dat HOSPITAL-SERVERS (Netplan, dnsmasq, Docker, Mock IoT HTTP)
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook -i $(INVENTORY) $(PLAYBOOK_DIR)/02_servers_base.yml

deploy-step1: deploy-core deploy-servers ## Trien khai tron bo Buoc 1 (Core Cisco + HOSPITAL-SERVERS)

verify-step1: ## Xac thuc tu dong VLAN, HSRP, ACL Zero-Trust & dich vu Server
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook -i $(INVENTORY) $(PLAYBOOK_DIR)/99_verify_step1.yml

deploy-hospital-apps: ## Trien khai Server 3 Hospital Apps (EHR/PACS RBAC API :8080 + MQTT :1883)
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook -i $(INVENTORY) $(PLAYBOOK_DIR)/03_hospital_apps.yml

verify-hospital-apps: ## Kiem thu tu dong Server 3 (RBAC 401/403/200, Offline /ui & MQTT :1883)
	ANSIBLE_CONFIG=$(ANSIBLE_CFG) ansible-playbook -i $(INVENTORY) $(PLAYBOOK_DIR)/98_verify_hospital_apps.yml
