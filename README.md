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
│       │   ├── member2_local/       # TH3: Máy Member 2 (192.168.100.0/24 - Đổi theo VMnet8 máy Member 2)
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
6. **Khóa Hợp đồng JSON (`contracts/`) & Tách 4 Profile (`inventories/`):** Giúp chạy ngay trên máy Member 1 (`member1_local`), Member 2 (`member2_local`), laptop 16GB (`lead_lite`), và sẵn sàng chuyển lên Server Trường/Cloud (`cloud_full`) không cần sửa playbook.

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

### B. Chọn 1 trong 2 cách thiết lập Control Node chạy Ansible

#### Cách 1 (Khuyên dùng cho mọi máy Windows/VMware — Không cần cài WSL 1)
Dùng chính VM **Ubuntu Server 24.04 (`HOSPITAL-SERVERS`)** làm nơi chạy Ansible + Docker (tránh hoàn toàn xung đột Hyper-V/WSL 2 với VMware Workstation và chạy được cả Bước 2–5 trên cùng 1 VM):

1. Tạo VM `HOSPITAL-SERVERS` (`2 vCPU`, `2 GB RAM`, `20 GB Disk`, tích chọn `Install OpenSSH server`), gắn 2 card mạng:
   - Card 1 (`ens33`): `Custom -> VMnet2` (Host-only, tắt DHCP — nối vào `Cloud1` / `VLAN 200`).
   - Card 2 (`ens34`): `NAT` (`VMnet8` — có Internet và chung dải quản trị OOB với EVE-NG).
2. Xem IP quản trị của VM (`ip -4 a show ens34`), rồi SSH từ Windows PowerShell vào (`ssh labadmin@<IP_ENS34>`) và cài môi trường 1 lần:

```bash
sudo apt update && sudo apt install -y git make python3-venv python3-pip sshpass
git clone <URL_REPO_GITHUB_CUA_NHOM> ~/hospital-zta-sdn-fl
cd ~/hospital-zta-sdn-fl

python3 -m venv ~/iac_venv
source ~/iac_venv/bin/activate
pip install --upgrade pip
pip install "paramiko<4.0" ansible netmiko pyyaml yamllint
ansible-galaxy collection install -r infra/ansible/requirements.yml
```

#### Cách 2 (Dành cho máy đã cài sẵn Ubuntu WSL 1 như Member 1)
> **Lưu ý:** Chỉ bật tính năng `Windows Subsystem for Linux` (**WSL 1**), **tuyệt đối không bật `VirtualMachinePlatform` / WSL 2 / Hyper-V** để tránh VMware EVE-NG bị lỗi `VT-x/EPT`.

```bash
sudo apt update && sudo apt install -y git make python3-venv python3-pip sshpass
git clone <URL_REPO_GITHUB_CUA_NHOM> ~/hospital-zta-sdn-fl
cd ~/hospital-zta-sdn-fl

python3 -m venv ~/iac_venv
source ~/iac_venv/bin/activate
pip install "paramiko<4.0" ansible netmiko pyyaml yamllint
ansible-galaxy collection install -r infra/ansible/requirements.yml
```

> **Lưu ý cho Member 1 nếu user trên VM `HOSPITAL-SERVERS` không phải `labadmin` (ví dụ `lemin`):**
> - Các lệnh chỉ SSH vào 7 Switch Cisco (`make check-lab`, `make reset-cisco`, `make deploy-core`) **không cần** đổi user.
> - Các lệnh cấu hình/kiểm tra `HOSPITAL-SERVERS` (`make deploy-servers`, `make deploy-step1`, `make verify-step1`) cần đặt trước biến môi trường **`export SERVER_USER=lemin`** trong phiên terminal đó (hoặc truyền `SERVER_USER=lemin make ...`).

### C. Cập nhật IP & Chạy triển khai / kiểm thử trên Lab thật

1. Mở `infra/ansible/inventories/<profile>/hosts.ini` (`member1_local`, `member2_local`, `lead_lite`, hoặc `cloud_full`), sửa dòng `HOSPITAL-SERVERS ansible_host=...` cho khớp với **IP của card `ens34`** trên VM `HOSPITAL-SERVERS` (xem bằng lệnh `ip -4 a show ens34`).
2. Kích hoạt `source ~/iac_venv/bin/activate` trong `~/hospital-zta-sdn-fl` và chạy theo profile tương ứng:

> **Hướng dẫn nhanh cho Member 2 (chạy độc lập bằng `ENV=member2_local`):**
> 1. Sau khi `git pull`, kiểm tra dải `VMnet8` (NAT) trên máy bạn (trong VMware *Virtual Network Editor* hoặc lệnh `ip -4 a show ens34` trên VM Ubuntu).
> 2. Thay dải mẫu `192.168.100` trong cả `infra/ansible/inventories/member2_local/hosts.ini` và `oob_network` của `infra/ansible/inventories/member2_local/group_vars/all.yml` bằng subnet `VMnet8` thực tế của máy bạn (và điền đúng IP `ens34` vào dòng `HOSPITAL-SERVERS`).
> 3. Nếu máy có 16GB RAM, có thể tạm thêm dấu `#` trước `SW-CORE-02`, `SW-BLD-A`, `SW-BLD-B`, `SW-DMZ` trong `member2_local/hosts.ini`; sau đó chạy toàn bộ các lệnh bên dưới với `ENV=member2_local`.

```bash
# Nếu user VM HOSPITAL-SERVERS khác 'labadmin' (ví dụ Member 1 dùng 'lemin'):
# export SERVER_USER=lemin

# 1. Kiểm tra Ping, SSH & HSRP tới các Switch trong profile
make check-lab ENV=member1_local

# 2. Kiểm tra cú pháp toàn bộ Ansible Playbook
make syntax-check ENV=member1_local

# 3. (Tùy chọn) Đưa 7 Switch về trạng thái trắng flash:bootstrap.cfg
make reset-cisco ENV=member1_local

# 4. Triển khai toàn bộ Core Cisco + cấu hình tự động HOSPITAL-SERVERS
make deploy-step1 ENV=member1_local

# (Hoặc chỉ test riêng phần cấu hình HOSPITAL-SERVERS khi chưa nạp image Cisco):
# make deploy-servers ENV=lead_lite

# 5. Chạy bộ kiểm thử xác thực tự động Switch + ACL + Server
make verify-step1 ENV=member1_local
```

### D. Xử lý nhanh 3 lỗi thực tế thường gặp ở Bước 1

1. **`apt` tải rất chậm trên `vn.archive.ubuntu.com`:** Đổi mirror về máy chủ nhanh trong nước rồi cài lại:
   ```bash
   sudo sed -i 's/vn\.archive\.ubuntu\.com/mirror.bizflycloud.vn/g' /etc/apt/sources.list.d/ubuntu.sources
   sudo apt update
   ```
2. **Lỗi `dpkg frontend lock` / `Waiting for cache lock` (do `unattended-upgrades` chạy ngầm khi mới cài Ubuntu):**
   ```bash
   sudo systemctl stop unattended-upgrades
   sudo dpkg --configure -a
   ```
3. **Lỗi `/usr/bin/env: 'bash\r': No such file or directory` khi chạy `make check-lab`:**
   ```bash
   sed -i 's/\r$//' scripts/check_lab.sh
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
- [x] `make deploy-servers ENV=lead_lite` chạy thực tế thành công trên `HOSPITAL-SERVERS` (`ok=14 changed=11 failed=0`, `dnsmasq` + `HTTP 200` `:8080`).
- [ ] Export file `.unl` từ EVE-NG đặt vào `infra/eveng/` (Member 1 thực hiện).
- [ ] Chạy `make deploy-step1 ENV=<profile>` và `make verify-step1 ENV=<profile>` trên đủ 7 Switch Cisco đạt `failed=0`.
- [ ] Kiểm thử trên `VPCS`: Guest (`VLAN 230`) **không** ping/TCP/UDP được sang Bác sĩ (`VLAN 10`) và Data Center (`VLAN 200`); IoMT (`VLAN 300`) truy cập được `.200.12:8080` nhưng bị chặn sang Bác sĩ, OOB và Internet; HSRP failover hoạt động khi tắt `SW-CORE-01`.
- [ ] GitHub Actions CI chạy xanh trên nhánh `main`.
