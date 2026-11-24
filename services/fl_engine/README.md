# Federated Learning IDS Engine (`services/fl_engine/`)

- **Phụ trách chính:** Member 2 (AI / Federated Learning)
- **Vị trí triển khai:**
  - `Server 2` (`192.168.200.11`): Flower (`flwr`) FedAvg Aggregator
  - `Edge A`, `Edge B`, `Edge IoMT`: Local Inference (`CNN + BiLSTM`) + Flower Client
- **Giai đoạn hiện thực:** Chạy song song từ Tuần 1 (Bước 4) và ghép vào lab ở Bước 5
- **Contract tuân thủ:** [contracts/alert_schema.json](../../contracts/alert_schema.json)

## Thành phần dự kiến
1. Pipeline tiền xử lý tập **Edge-IIoTset / TON_IoT** đồng bộ với bộ trích xuất đặc trưng live (`NFStream`/Scapy).
2. Mô hình PyTorch **CNN + BiLSTM** huấn luyện Non-IID trên 3 phân khu và tổng hợp FedAvg qua mTLS.
3. Worker gửi `EdgeFLAlert` JSON về `https://192.168.200.10:8443/api/v1/alerts` khi độ tin cậy vượt ngưỡng.
