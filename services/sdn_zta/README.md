# SDN Controller & ZTA Policy Engine (`services/sdn_zta/`)

- **Phụ trách chính:** Nhóm trưởng
- **Vị trí triển khai:** `Server 1` (`192.168.200.10` - Data Center VLAN 200)
- **Giai đoạn hiện thực:** Bước 2 & Bước 5
- **Contract tuân thủ:** [contracts/alert_schema.json](../../contracts/alert_schema.json) và [contracts/enforcement_schema.json](../../contracts/enforcement_schema.json)

## Thành phần dự kiến
1. **SDN Controller (`os-ken` / Ryu OpenFlow 1.3):** Nghe kết nối OpenFlow trên cổng `6653` từ các OVS PEP (`OVS-IOMT`, `OVS-BLD-A`, `OVS-BLD-B`) và cung cấp REST API cài/gỡ flow chặn động.
2. **ZTA Policy Engine & Policy Administrator (FastAPI):** Nhận cảnh báo đã xác thực từ Edge FL-IDS, đối chiếu ngữ cảnh danh tính từ `Server 4`, ra quyết định `QUARANTINE` / `RATE_LIMIT` / `RELEASE` và đẩy log về Wazuh.
