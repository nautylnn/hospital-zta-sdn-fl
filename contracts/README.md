# Hợp đồng Giao tiếp JSON giữa các Nhóm (Interface Contracts)

Thư mục này khóa cứng cấu trúc dữ liệu trao đổi giữa **Member 2 (AI / Federated Learning Edge)** và **Nhóm trưởng (ZTA Policy Engine + SDN Controller trên Server 1)**. Nhờ 2 schema này, hai nhóm có thể code và viết unit test song song ngay từ Tuần 1 mà không cần đợi ghép lab mới sửa API.

## 1. Luồng Cảnh báo: Edge FL-IDS $\rightarrow$ ZTA Policy Engine (`alert_schema.json`)

- **Endpoint:** `POST https://192.168.200.10:8443/api/v1/alerts` (yêu cầu mTLS ở Bước 5; giai đoạn test dùng Header token).
- **Ví dụ payload hợp lệ từ `edge-iomt`:**

```json
{
  "alert_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-11-24T00:15:00Z",
  "edge_id": "edge-iomt",
  "switch_dpid": "0000000000000003",
  "src_mac": "00:50:79:66:68:04",
  "src_ip": "192.168.180.15",
  "dst_ip": "192.168.10.20",
  "vlan_id": 300,
  "attack_type": "DDoS_TCP_Flood",
  "confidence": 0.96,
  "model_round": 12,
  "features_summary": {
    "packet_rate": 1420.5,
    "byte_count": 98400,
    "duration_ms": 500
  }
}
```

## 2. Luồng Thực thi: ZTA Policy Administrator $\rightarrow$ SDN Controller (`enforcement_schema.json`)

- **Endpoint:** `POST http://127.0.0.1:8081/sdn/quarantine` (nội bộ trên `Server 1` tới OS-Ken/Ryu REST API).
- **Ví dụ payload hợp lệ:**

```json
{
  "decision": "QUARANTINE",
  "switch_dpid": "0000000000000003",
  "match_mac": "00:50:79:66:68:04",
  "match_ip": "192.168.180.15",
  "vlan_id": 300,
  "ttl_seconds": 120,
  "priority": 50000,
  "reason": "High-confidence FL-IDS alert (DDoS_TCP_Flood, conf=0.96)",
  "alert_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
