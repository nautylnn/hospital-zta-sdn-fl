# DMZ WAF, Public Web & Public DNS (`services/dmz_waf/`)

- **Phụ trách chính:** Member 1 (Hạ tầng Mạng, NGFW & WAF)
- **Vị trí triển khai:** Phân khu `DMZ` (`VLAN 210` - nối vào `SW-DMZ` & cổng DMZ của Firewall `U3`)
  - Public Web + WAF: `192.168.210.3`
  - Public DNS: `192.168.210.4`
- **Giai đoạn hiện thực:** Bước 3

## Thành phần dự kiến
1. **Nginx + ModSecurity v3 (OWASP Core Rule Set):** Chặn SQL Injection, XSS và các tấn công ứng dụng Web HTTP/HTTPS trước khi vào Public Web.
2. **CoreDNS:** Phân giải tên miền công khai cho DMZ và kiểm thử chính sách Firewall giữa DMZ và Data Center.
