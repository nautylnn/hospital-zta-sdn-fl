# Hospital Applications & Data Center Services (`services/hospital_apps/`)

- **Phụ trách chính:** Member 1 (phối hợp cùng Nhóm trưởng)
- **Vị trí triển khai:** `Server 3` (`192.168.200.12` - Data Center `VLAN 200` trên VM `HOSPITAL-SERVERS`)
- **Trạng thái hiện tại:**
  - ✅ **Bước 1:** Tự động hóa `dnsmasq` (DHCP Relay cho toàn bệnh viện) + `mock-iot-http` (`:8080`) qua `02_servers_base.yml`.
  - ✅ **Bước 2:** Nâng cấp thành **EHR/PACS RBAC API + Web UI offline (`/ui`)** trên cổng `:8080` và **Eclipse Mosquitto MQTT Broker** trên cổng `:1883`, đóng gói bằng Docker Compose và tự động hóa qua `03_hospital_apps.yml` / `98_verify_hospital_apps.yml`.

---

## 1. Cấu trúc thư mục

```text
services/hospital_apps/
├── README.md
├── docker-compose.yml              # Khởi chạy ehr-api (:8080) & mosquitto (:1883) trên 192.168.200.12
├── ehr_api/
│   ├── Dockerfile                  # Python 3.11-slim + FastAPI + Uvicorn + Pydantic
│   └── app.py                      # API phân quyền RBAC (401/403/200) + giao diện HTML offline /ui
└── mosquitto/
    └── config/
        └── mosquitto.conf          # Listener 1883 (0.0.0.0), allow_anonymous true
```

---

## 2. Triển khai & Kiểm thử tự động qua `Makefile`

Chạy từ thư mục gốc repo `~/hospital-zta-sdn-fl` (sau khi đã kích hoạt `~/iac_venv` và đã chạy `make deploy-servers ENV=<profile>` ít nhất 1 lần để có IP `192.168.200.12`):

```bash
# Triển khai Server 3 (tắt mock-iot-http, copy vào /opt/hospital-apps, build & start Docker Compose)
make deploy-hospital-apps ENV=member1_local

# Kiểm thử tự động toàn bộ Server 3 (Container, Health /, /ui, RBAC 401/403/200 & MQTT Pub/Sub :1883)
make verify-hospital-apps ENV=member1_local
```

> **Lưu ý:** Lệnh `make verify-step1 ENV=<profile>` đã được cập nhật để chấp nhận cả `mock-iot-http` (Bước 1) lẫn container `hospital-ehr-api` (Bước 2) trên cổng `:8080`, nên không cần tắt Server 3 khi chạy kiểm thử Bước 1.

---

## 3. Danh sách Endpoint & Phân quyền RBAC (`192.168.200.12:8080`)

| Method & Path | Mô tả | Token / Vai trò được phép | Mã HTTP |
| --- | --- | --- | --- |
| `GET /` | Health check (`status: ok`) | Công khai nội bộ | `200` |
| `GET /ui` | Giao diện Web UI bệnh viện 100% offline | Công khai nội bộ | `200` |
| `GET /api/v1/ehr/patients` | Xem danh sách bệnh án EHR (`BN-001`, `BN-002`) | Chỉ `doctor` | `200` (`doctor`), `403` (`nurse`/`iomt`), `401` (thiếu/sai token) |
| `POST /api/v1/iomt/telemetry` | Thiết bị IoMT đẩy dữ liệu sinh hiệu (`device_id`, `heart_rate`, `spo2`) | `iomt`, `nurse`, `doctor` | `200` (hợp lệ), `401` (thiếu/sai token) |
| `GET /api/v1/iomt/telemetry` | Xem 20 bản ghi sinh hiệu gần nhất | `doctor`, `nurse` | `200` (`doctor`/`nurse`), `403` (`iomt`), `401` (thiếu/sai token) |

### Bearer Token mẫu (Demo Bước 2 — Bước 5 chuyển sang JWT/mTLS từ Server 4)
- **Bác sĩ (`doctor`):** `Bearer doctor-token-123`
- **Y tá (`nurse`):** `Bearer nurse-token-456`
- **Thiết bị IoMT (`iomt`):** `Bearer iomt-token-789`

---

## 4. Cách kiểm thử trên Lab EVE-NG & Trình duyệt

1. **Từ `VPCS` trong EVE-NG (kiểm chứng xuyên Switch & Cisco ACL):**
   - Trên **`IOMT-MONITOR` (`VLAN 300`)** hoặc **`PC-BLD-A` (`VLAN 10`)**:
     ```text
     ping 192.168.200.12 -P 6 -p 8080
     ping 192.168.200.12 -P 6 -p 1883
     ```
     -> Kết nối thành công (ACL `IOMT_ZTA_BASELINE` mở sẵn TCP `8080` và `1883` tới `192.168.200.12`).
   - Trên **`PC-GUEST-A` (`VLAN 230`)**: cùng lệnh trên sẽ bị **timeout** do ACL `GUEST` chặn.
2. **Mở Web UI từ trong EVE-NG (100% offline):**
   - Dùng node Linux Desktop (ví dụ `linux-slax`) nối vào VLAN lâm sàng (`VLAN 10`/`20`) hoặc IoMT (`VLAN 300`), mở trình duyệt vào:
     `http://192.168.200.12:8080/ui`
3. **Mở nhanh từ trình duyệt Windows (qua SSH Tunnel):**
   ```powershell
   ssh -L 8080:192.168.200.12:8080 lemin@<IP_ENS34_HOSPITAL_SERVERS>
   ```
   Sau đó truy cập `http://localhost:8080/ui` hoặc `http://localhost:8080/docs`.
