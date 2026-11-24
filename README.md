# Hospital Zero-Trust, SDN & Federated Learning IDS (`hospital-zta-sdn-fl`)

Kho mã nguồn mở **Infrastructure as Code (IaC)** cho đồ án tốt nghiệp xây dựng kiến trúc phòng thủ chủ động bệnh viện tích hợp **NGFW + WAF + Zero-Trust (ZTA) + SDN (OpenFlow/OVS) + Federated Learning IDS (CNN + BiLSTM / Flower) + SIEM/PKI/RADIUS**.

Repo này hợp nhất toàn bộ nền tảng mạng Cisco & Ansible từ giai đoạn đầu của nhóm thành **Bước 1 (Khung Pipeline Chung)**, giúp cả 3 thành viên làm việc song song và chuyển đổi mượt mà giữa **Laptop cá nhân 16GB (`TH3`)**, **Server Trường (`TH1`)** và **Cloud VM (`TH2`)**.

---

## 1. Cấu trúc Monorepo

```text
hospital-zta-sdn-fl/
├── Makefile                         # Điểm vào lệnh ngắn gọn (truyền ANSIBLE_CONFIG tự động)
├── .yamllint.yml                    # Quy tắc kiểm tra cú pháp YAML
├── .env.example                     # Mẫu biến môi trường đăng nhập lab (không commit mật khẩu thật)
├── design/
│   └── network_spec.yml             # [SSOT] Nguồn chân lý duy nhất: 12 VLAN, HSRP, DHCP, ACL, Ports
├── contracts/
│   ├── alert_schema.json            # Hợp đồng JSON: Edge FL-IDS -> Server 1 ZTA Policy Engine
│   └── enforcement_schema.json      # Hợp đồng JSON: ZTA PA -> SDN Controller (OS-Ken/Ryu)
├── infra/
│   ├── eveng/README.md              # Hướng dẫn đấu nối EVE-NG & Day-0 Bootstrap Cisco
│   └── ansible/
│       ├── ansible.cfg
│       ├── requirements.yml         # cisco.ios, ansible.posix
│       ├── inventories/
│       │   ├── member1_local/       # TH3: Máy Member 1 (192.168.139.0/24 - Full 7 Switch)
│       │   ├── lead_lite/           # TH3: Laptop 16GB Nhóm trưởng (192.168.5.0/24 - Nhánh gọn)
│       │   └── cloud_full/          # TH1a/TH2: Server Trường / Cloud (10.99.0.0/24 + Tailscale)
│       ├── templates/
│       │   ├── 60-hospital-vlan200.yaml.j2
│       │   ├── dnsmasq.conf.j2
│       │   └── mock-iot-http.service.j2
│       └── playbooks/
│           ├── 00_reset_cisco.yml   # Trả 7 Switch về flash:bootstrap.cfg (serial: 2)
│           ├── 01_core_cisco.yml    # Đẩy VLAN, Trunk/Access, HSRP, STP, ACL & khóa VTY SSH
│           ├── 02_servers_base.yml  # Tự động hóa HOSPITAL-SERVERS (Netplan, dnsmasq, Docker, HTTP)
│           └── 99_verify_step1.yml  # Kiểm thử tự động toàn bộ Switch + Server
├── services/                        # Khung code từng phân hệ (triển khai ở Bước 2-5)
│   ├── sdn_zta/                     # Server 1 (.200.10) - Nhóm trưởng
│   ├── fl_engine/                   # Server 2 (.200.11) & Edges - Member 2
│   ├── dmz_waf/                     # DMZ (.210.3-.4) - Member 1
│   ├── hospital_apps/               # Server 3 (.200.12) - Member 1 & Nhóm trưởng
│   └── security_ops/                # Server 4 (.200.13) - Nhóm trưởng
├── experiments/                     # Kịch bản tcpreplay & benchmark Chương 5 - Member 2
├── scripts/
│   ├── validate_design.py           # Kiểm tra SSOT, bảo mật ACL, JSON schema & đường dẫn (offline)
│   └── check_lab.sh                 # Kiểm tra nhanh ICMP Ping, SSH & HSRP theo từng profile
└── .github/workflows/ci.yml         # CI tự động kiểm tra YAML, Python validator & Ansible syntax
```

---

## 2. Những nâng cấp & bản vá đã thực hiện ở Bước 1

So với bản triển khai ban đầu trong `hospital_network/`, Bước 1 đã tích hợp nguyên vẹn lõi IaC của Member 1 và xử lý dứt điểm 6 điểm sau:

1. **Vá lỗ hổng ACL `GUEST`:** Chuyển từ chặn lẻ `icmp`/`tcp` sang **`deny ip`** toàn bộ dải nội bộ `192.168.0.0/16`, dải `oob_network`, `10.0.0.0/8` và `172.16.0.0/12` (chỉ mở unicast DHCP renew tới `.200.12` và Internet).
2. **Siết chuẩn Zero-Trust cho `IOMT_ZTA_BASELINE`:** Xóa bỏ dòng `permit ip any any` ở cuối, thay bằng **`deny ip any any log`** (Default-Deny), chỉ mở đúng cổng dịch vụ y tế (`8080`, `443`, `1883` tới Server 3 và `1514`, `1515` tới Wazuh Server 4).
3. **Bảo vệ vùng quản trị OOB (`VLAN 999`):** Thêm ACL `CLINICAL_PROTECT_OOB` lên các VLAN lâm sàng (`10, 20, 30, 60, 70, 80`) và áp dụng Standard ACL **`OOB_VTY_ONLY`** lên `line vty 0 15` của cả 7 Switch (chỉ nhận SSH từ OOB hoặc Tailscale CGNAT).
4. **Chuẩn hóa số liệu SSOT:** Sửa thống nhất **12 VLAN**, chuẩn hóa DMZ là **`VLAN 210`**, xóa bỏ đường dẫn tuyệt đối cá nhân trong `~/.bashrc`, tách `ansible_connection` sạch giữa Switch Cisco và Linux Server.
5. **Tự động hóa `HOSPITAL-SERVERS` (`02_servers_base.yml`):** Biến các bước gõ tay trước đây (Netplan `.200.10`–`.13`, `dnsmasq` cho tất cả client VLAN, Docker, dịch vụ Mock IoT HTTP) thành playbook Jinja2 chạy trực tiếp từ `design/network_spec.yml`.
6. **Khóa Hợp đồng JSON (`contracts/`) & Tách 3 Profile (`inventories/`):** Giúp chạy ngay trên máy 16GB (`lead_lite` / `member1_local`) và sẵn sàng chuyển lên Server Trường/Cloud (`cloud_full`) không cần sửa playbook.

---

## 3. Hướng dẫn cài đặt & chạy Bước 1

### A. Kiểm tra offline trên máy Windows hoặc Linux (Không cần bật EVE-NG)

Trên Windows PowerShell:
```powershell
py scripts/validate_design.py
```

Trên Linux / WSL:
```bash
make validate
```

### B. Cài đặt Control Node (Ubuntu WSL 1 hoặc Linux)

> **Lưu ý trên Windows chạy VMware Workstation:** Dùng **Ubuntu WSL 1** (không bật WSL 2/Hyper-V) để tránh xung đột Nested Virtualization với EVE-NG.

```bash
python3 -m venv ~/iac_venv
source ~/iac_venv/bin/activate
pip install "paramiko<4.0" ansible netmiko pyyaml yamllint
ansible-galaxy collection install -r infra/ansible/requirements.yml
```

### C. Chạy triển khai & kiểm thử trên Lab thật (chọn `ENV=member1_local`, `lead_lite` hoặc `cloud_full`)

```bash
# 1. Kiểm tra Ping, SSH & HSRP tới toàn bộ thiết bị trong profile
make check-lab ENV=member1_local

# 2. Kiểm tra cú pháp toàn bộ Ansible Playbook
make syntax-check ENV=member1_local

# 3. (Tùy chọn) Đưa 7 Switch về trạng thái trắng flash:bootstrap.cfg
make reset-cisco ENV=member1_local

# 4. Triển khai toàn bộ Core Cisco + cấu hình tự động HOSPITAL-SERVERS
make deploy-step1 ENV=member1_local

# 5. Chạy bộ kiểm thử xác thực tự động Switch + ACL + Server
make verify-step1 ENV=member1_local
```

---

## 4. Đưa lên GitHub cho nhóm 3 người

```bash
git init
git add .
git commit -m "feat(step1): unified open-source IaC foundation and security hardening"
git branch -M main
git remote add origin <URL_REPO_GITHUB_CUA_NHOM>
git push -u origin main
```

Sau khi push, mở tab **Actions** trên GitHub để xác nhận workflow `Hospital ZTA-SDN-FL CI` chạy xanh. Từ thời điểm này, mọi thành viên phải tạo nhánh riêng (`feat/ngfw-waf`, `feat/fl-engine`, `feat/sdn-zta`) và mở Pull Request về `main`.

---

## 5. Checklist Nghiệm thu Bước 1 (Definition of Done)

- [x] `py scripts/validate_design.py` đạt `ALL CHECKS PASSED (0 failures)` offline.
- [ ] Export file `.unl` từ EVE-NG đặt vào `infra/eveng/` (Member 1 thực hiện).
- [ ] Chạy `make deploy-step1 ENV=<profile>` và `make verify-step1 ENV=<profile>` trên lab thật đạt `failed=0`.
- [ ] Kiểm thử trên `VPCS`: Guest (`VLAN 230`) **không** ping/TCP/UDP được sang Bác sĩ (`VLAN 10`) và Data Center (`VLAN 200`); IoMT (`VLAN 300`) truy cập được `.200.12:8080` nhưng bị chặn sang Bác sĩ, OOB và Internet; HSRP failover hoạt động khi tắt `SW-CORE-01`.
- [ ] GitHub Actions CI chạy xanh trên nhánh `main`.
