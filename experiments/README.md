# Kịch bản Tấn công & Đo đạc Thực nghiệm Chương 5 (`experiments/`)

- **Phụ trách chính:** Member 2 (phối hợp cả nhóm ở Bước 6)
- **Giai đoạn hiện thực:** Bước 5 & Bước 6

## Các bộ đo đạc dự kiến cho Luận văn
1. **Đánh giá AI (`5.3`):** Accuracy, Precision, Recall, F1-Score (FL `FedAvg` vs Centralized Baseline) và đường cong hội tụ Non-IID.
2. **Đánh giá Mạng & ZTA (`5.4`):**
   - Độ trễ mạng (`Network Latency`) trước/sau khi áp dụng OpenFlow Quarantine.
   - Chi phí truyền thông (`Communication Overhead` MB/round) của Flower qua `VLAN 999`.
   - Thời gian phản hồi IPS (`IPS Response Time = t3 - t0`) khi phát lại tấn công bằng `tcpreplay`.
