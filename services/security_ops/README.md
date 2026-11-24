# Security Operations: SIEM, Identity & PKI (`services/security_ops/`)

- **Phụ trách chính:** Nhóm trưởng
- **Vị trí triển khai:** `Server 4` (`192.168.200.13` - Data Center VLAN 200)
- **Giai đoạn hiện thực:** Bước 5 (chạy test module trước trên profile mạnh hoặc server riêng)

## Thành phần dự kiến
1. **Step-CA (PKI):** Cấp phát chứng chỉ mTLS cho `Edge A/B/IoMT`, `Server 1`, và `Server 2`.
2. **FreeRADIUS:** Quản lý danh tính thiết bị/tài khoản (Clinical, Guest, IoMT) hỗ trợ ZTA Policy Engine và kiểm thử 802.1X.
3. **Wazuh SIEM:** Thu thập log tập trung từ NGFW (`U3`), WAF (`DMZ`), Edge FL-IDS và ZTA Policy Engine.
