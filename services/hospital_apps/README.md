# Hospital Applications & Data Center Services (`services/hospital_apps/`)

- **Phụ trách chính:** Member 1 (phối hợp cùng Nhóm trưởng)
- **Vị trí triển khai:** `Server 3` (`192.168.200.12` - Data Center VLAN 200)
- **Trạng thái hiện tại:**
  - ✅ **Bước 1:** Đã tự động hóa `dnsmasq` (DHCP Relay cho toàn bệnh viện) + `mock-iot-http` (`:8080`) qua Ansible playbook `02_servers_base.yml`.
  - ⏳ **Bước 2:** Nâng cấp lên EHR/PACS API có xác thực phân quyền (`401`/`403`/`200`) và MQTT broker (`Mosquitto :1883`) cho thiết bị IoMT.
