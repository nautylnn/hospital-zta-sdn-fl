# TỔNG HỢP LÝ THUYẾT, ĐỊNH NGHĨA & KHUNG PIPELINE ĐỒ ÁN (`hospital-zta-sdn-fl`)

> **Mục đích tài liệu:** Sổ tay tra cứu toàn bộ khái niệm, định nghĩa học thuật, ví dụ thực tế, bản thiết kế 2 Pipeline (Build & Runtime), lộ trình 6 bước hiện thực, ánh xạ mã nguồn trong repo và bộ câu hỏi phản biện Hội đồng dành cho **Nhóm trưởng** để ôn tập và review cùng thành viên.

---

## PHẦN 1: BỨC TRANH TỔNG QUAN HAI PIPELINE CỦA ĐỒ ÁN

Để làm chủ toàn bộ hệ thống gồm nhiều mảng công nghệ khác nhau, hãy tách tư duy thành **2 đường ống (Pipeline)** rõ ràng:

### 1.1. Build Pipeline (Đường ống Xây dựng — IaC & CI/CD)
Quy trình tự động biến toàn bộ file cấu hình và mã nguồn trên GitHub thành hệ thống mạng bệnh viện chạy thật thông qua `Makefile`:

```text
[GitHub Monorepo] ──(GitHub Actions: validate_design.py + yamllint + syntax-check)──>
  │
  ├── Tầng 0 (Hạ tầng): Dựng Lab EVE-NG (.unl) + VM HOSPITAL-SERVERS (Cloud0 + Cloud1)
  ├── Tầng 1 (Core Campus): Ansible đẩy 12 VLAN, HSRP, STP, Zero-Trust ACL & VTY lên Cisco Switches
  ├── Tầng 2 (Biên & DMZ): Ansible/API cấu hình Border Router (U1) + OPNsense NGFW (U3) + DMZ WAF
  ├── Tầng 3 (SDN Access & SPAN): Ansible đẩy Open vSwitch (OVS) + OpenFlow về Server 1 + bật SPAN sang Edge
  ├── Tầng 4 (DC & Edge Services): Docker Compose bật ZTA PE/PA, OS-Ken, Flower FL, EHR, Wazuh, FreeRADIUS, PKI
  └── Tầng 5 (Verify & Benchmark): Chạy Ansible Verify + Kịch bản tấn công (tcpreplay) + Xuất số liệu Chương 5
```

### 1.2. Runtime Pipeline (Đường ống Vận hành — Phòng thủ chủ động khép kín)
Luồng xử lý lưu lượng và phản ứng tự động khi hệ thống đã chạy và xuất hiện tấn công:

```text
[1. Nguồn lưu lượng]
  - Ngoài vào: Internet / Branch (GRE/IPsec) ──> U1 Border ──> U3 NGFW ──> DMZ WAF (VLAN 210)
  - Nội bộ / IoMT: Client / Thiết bị y tế ──> OVS Access/Dist PEP
                                                  │
                               (Bản sao gói tin   │ SPAN)
                                                  ▼
[2. Phát hiện & Học liên kết tại Biên]  [Edge A / Edge B / Edge IoMT]
  - Trích đặc trưng luồng (NFStream) ──> CNN + BiLSTM Inference (PyTorch)
  - Định kỳ gửi trọng số (mTLS) <──────> Server 2 (192.168.200.11): Flower FedAvg Aggregator
                                                  │
                               (Authenticated     │ Alert JSON qua mTLS / JWT)
                                                  ▼
[3. Quyết định Zero-Trust]              [Server 1 (192.168.200.10): ZTA Policy Engine + PA]
  - Đối chiếu danh tính / ngữ cảnh từ Server 4 (192.168.200.13: FreeRADIUS / PKI)
  - Ra quyết định: ALLOW / RATE_LIMIT / QUARANTINE (TTL 60–300s) / RELEASE
                                                  │
                               (OpenFlow 1.3      │ từ OS-Ken / Ryu)
                                                  ▼
[4. Thực thi & Ghi nhận]
  - OVS PEP cài flow rule DROP MAC/IP kẻ tấn công ngay tại tầng Access (chặn di chuyển ngang L2/L3)
  - Toàn bộ log (NGFW + WAF + Edge AI + ZTA + OpenFlow) đổ tập trung về Server 4 (Wazuh SIEM)
```

---

## PHẦN 2: TOÀN BỘ ĐỊNH NGHĨA & KIẾN THỨC THEO 6 NHÓM

### NHÓM 1: QUẢN TRỊ DỰ ÁN, IaC & PIPELINE (CÁCH XÂY HỆ THỐNG)

#### 1. Build Pipeline vs. Runtime Pipeline
* **Build Pipeline (IaC / CI-CD):** Quy trình tự động biến các file mã nguồn (YAML, Python, Ansible, Docker) trên GitHub thành một hạ tầng mạng chạy hoàn chỉnh. *Ví dụ đời thường: Bản vẽ kỹ thuật và đội thi công tự động xây dựng nên tòa nhà bệnh viện.*
* **Runtime Pipeline:** Luồng đi của gói tin và sự phối hợp giữa các lớp bảo mật **khi tòa nhà đã vận hành và có kẻ tấn công**. *Ví dụ đời thường: Camera phát hiện đột nhập $\rightarrow$ báo phòng bảo vệ $\rightarrow$ cửa tự động khóa lại.*

#### 2. IaC (Infrastructure as Code) & Single Source of Truth (SSOT)
* **IaC:** Phương pháp mô tả và triển khai toàn bộ hạ tầng mạng/máy chủ bằng mã nguồn thay vì thao tác thủ công trên giao diện đồ họa (GUI) hay gõ tay từng lệnh CLI. Giúp hệ thống tái lập được trên máy khác và lưu vết thay đổi trên Git.
* **SSOT (Nguồn chân lý duy nhất — `design/network_spec.yml`):** Nguyên tắc lưu toàn bộ thông số lõi (12 VLAN, IP Gateway HSRP, DHCP pool, ACL, cổng cắm Switch, IP 4 DC Server) tại **1 file duy nhất**. Mọi Playbook, Template và Script kiểm thử đều đọc từ file này, tránh tình trạng mỗi thành viên cấu hình một kiểu.

#### 3. Ansible, Inventory, Playbook, Role & Tính lũy đẳng (Idempotent)
* **Ansible:** Công cụ tự động hóa chạy từ máy điều khiển (Control Node), kết nối qua SSH vào hàng loạt Switch và Linux Server để cấu hình đồng bộ mà không cần cài agent phức tạp lên thiết bị mạng.
* **Inventory (`hosts.ini` & `group_vars/all.yml`):** "Cuốn danh bạ" khai báo địa chỉ IP, phân nhóm thiết bị (`core_switches`, `access_switches`, `hospital_servers`) và biến môi trường. Khi chuyển giữa máy cá nhân (`lead_lite`, `member1_local`, `member2_local`) và Server Trường/Cloud (`cloud_full`), nhóm chỉ đổi profile inventory chứ không sửa logic Playbook.
* **Playbook & Role:** **Playbook** là kịch bản thực thi tuần tự các bước (ví dụ `01_core_cisco.yml`, `02_servers_base.yml`); **Role** là gói cấu hình tách riêng theo từng chức năng (NGFW, WAF, OVS, FL...) giúp 3 người code song song không xung đột file.
* **Idempotent (Tính lũy đẳng):** Đặc tính chạy Playbook **1 lần hay 10 lần liên tiếp đều cho ra cùng một trạng thái đích cuối cùng**. Thành phần nào đã đúng chuẩn thì Ansible bỏ qua (`ok`), thành phần nào thiếu hoặc sai lệch thì mới cập nhật (`changed`), tránh tạo cấu hình trùng lặp.

#### 4. Monorepo, CI/CD, Lint, Makefile, Docker & Bootstrap Day-0
* **Monorepo:** Gom toàn bộ mã nguồn Mạng, IaC, SDN/ZTA, WAF, AI/FL và Benchmark vào chung **1 kho GitHub duy nhất** để đồng bộ phiên bản và hợp đồng giao tiếp.
* **CI/CD & Lint / Syntax-check (`.github/workflows/ci.yml`):** Quy trình tự động kiểm tra mã nguồn mỗi khi có `git push` hoặc Pull Request. **Lint** (`yamllint`) bắt lỗi định dạng YAML; **`--syntax-check`** kiểm tra cú pháp Ansible; `validate_design.py` kiểm tra logic VLAN/IP/ACL trước khi cho phép merge vào nhánh `main`.
* **Makefile:** Công cụ rút gọn các câu lệnh dài (kèm tự động truyền biến `ANSIBLE_CONFIG`) thành lệnh ngắn như `make validate`, `make deploy-step1 ENV=lead_lite`, `make verify-step1`.
* **Docker & Docker Compose:** Đóng gói từng ứng dụng (OS-Ken, FastAPI ZTA, Flower, Nginx/ModSecurity, Wazuh...) cùng toàn bộ thư viện phụ thuộc vào các container cô lập, chạy đồng nhất trên mọi máy Linux.
* **Bootstrap Day-0 & Reset:** Cấu hình tối thiểu ban đầu trên Switch trắng (tạo hostname, tài khoản SSH v2, IP quản trị `Gi0/0`, lưu `flash:bootstrap.cfg`) để Ansible kết nối vào được. Playbook `00_reset_cisco.yml` khôi phục toàn bộ Switch về trạng thái trắng này (`serial: 2` để tránh quá tải CPU) phục vụ demo và kiểm thử lặp lại.

---

### NHÓM 2: HẠ TẦNG MẠNG BỆNH VIỆN (L2/L3, DỰ PHÒNG & CÔ LẬP)

#### 5. VLAN, Access Port và 802.1Q Trunk Port
* **VLAN (Virtual LAN):** Kỹ thuật chia một hạ tầng Switch vật lý thành nhiều mạng con cô lập ở tầng 2 (Layer 2). Ví dụ trong đồ án có **12 VLAN**: Lâm sàng Tòa A (`10, 20, 30`), Lâm sàng Tòa B (`60, 70, 80`), Data Center (`200`), DMZ (`210`), Wi-Fi Khách (`220, 230`), Thiết bị y tế IoMT (`300`), Quản trị OOB (`999`).
* **Access Port:** Cổng Switch nối trực tiếp xuống thiết bị đầu cuối (PC bác sĩ, Access Point khách, máy bơm tiêm IoMT, server), chỉ thuộc đúng **1 VLAN**.
* **802.1Q Trunk Port:** Cổng nối liên kết giữa Switch với Switch, cho phép nhiều VLAN đi chung trên một đường truyền bằng cách gắn thẻ nhãn (VLAN Tag) vào khung Ethernet. Trong đồ án, `trunk_allowed_vlans` (`10,20,30,60,70,80,200,220,230,300`) **tuyệt đối loại trừ `VLAN 210` (DMZ) và `VLAN 999` (OOB)**.

#### 6. Data Plane vs. OOB Management (`VLAN 999`)
* **Data Plane (Mặt phẳng dữ liệu):** Đường truyền lưu lượng nghiệp vụ của bác sĩ, bệnh nhân, khách và thiết bị IoMT.
* **OOB Management (Out-of-Band — Quản trị ngoài băng tần):** Mạng quản trị tách biệt hoàn toàn (`VLAN 999`), đi qua cổng quản trị riêng (`Gi0/0` nối `Cloud0` hoặc `Cloud1`), không đi chung đường Trunk dữ liệu. Dùng riêng cho Ansible SSH, điều khiển OpenFlow, trao đổi trọng số FL và đẩy log SIEM. Giúp bảo vệ hạ tầng điều khiển ngay cả khi Data Plane bị tấn công hoặc tắc nghẽn.

#### 7. SVI, Inter-VLAN Routing & DHCP Relay (`ip helper-address`)
* **SVI (Switch Virtual Interface):** Giao diện cổng định tuyến ảo trên Switch Layer 3 (`interface Vlan10`, `Vlan200`...), đóng vai trò Default Gateway (`.1`) cho các máy trong VLAN đó.
* **Inter-VLAN Routing:** Cơ chế định tuyến gói tin đi qua lại giữa các VLAN khác nhau (ví dụ Bác sĩ `VLAN 10` truy cập máy chủ bệnh án EHR ở `VLAN 200`).
* **DHCP Relay (`ip helper-address`):** Gói tin xin cấp IP (DHCP Discover) là gói Broadcast ở Layer 2 nên mặc định không đi qua được ranh giới VLAN/Router. Lệnh `ip helper-address 192.168.200.12` trên từng SVI khiến Core Switch chuyển tiếp yêu cầu xin IP về máy chủ `dnsmasq` tại `Server 3 (192.168.200.12)` để cấp phát IP tập trung cho toàn bệnh viện.

#### 8. HSRP Active/Active & STP PVST (Dự phòng & Chống lặp mạng)
* **HSRP (Hot Standby Router Protocol):** Giao thức dự phòng Gateway ảo giữa `SW-CORE-01` (`.2`) và `SW-CORE-02` (`.3`), cùng chia sẻ một IP Gateway ảo (VIP `.1`).
  * **Active/Active Load Balancing:** Chia đôi tải — `SW-CORE-01` làm Active (`priority 150`) cho Nhóm A (Tòa A + Data Center + Guest A), còn `SW-CORE-02` làm Active (`priority 150`) cho Nhóm B (Tòa B + Guest B + IoMT). Khi một Core Switch gặp sự cố, con còn lại tự động tiếp quản (Failover) nhờ cơ chế `preempt`.
* **STP PVST (Per-VLAN Spanning Tree):** Giao thức chống vòng lặp (Loop / Broadcast Storm) khi đấu nối liên kết dự phòng dạng vòng giữa Core và Distribution/Access Switch, đồng thời cân bằng tải Root Bridge theo từng nhóm VLAN khớp với HSRP (`priority 24576` cho Primary, `28672` cho Secondary).

#### 9. Extended ACL & Điểm mù "Di chuyển ngang" (Lateral Movement)
* **Extended ACL:** Danh sách kiểm soát truy cập lọc gói tin theo IP nguồn, IP đích, giao thức (`ip`, `tcp`, `udp`, `icmp`) và cổng dịch vụ (`8080`, `443`, `1883`, `bootps`).
  * *Lưu ý bảo mật đã vá trong repo:* ACL `GUEST` phải chặn toàn bộ giao thức (`deny ip`) vào mạng nội bộ `192.168.0.0/16` (thay vì chỉ chặn `icmp`/`tcp` dễ làm lọt UDP và nhánh Clinical); ACL `IOMT_ZTA_BASELINE` phải tuân thủ **Default-Deny** (kết thúc bằng `deny ip any any`, không dùng `permit ip any any` ra Internet).
* **Lateral Movement (Di chuyển ngang) & Điểm mù của Core ACL:** Kịch bản kẻ tấn công chiếm một thiết bị yếu (như camera IoMT ở `VLAN 300`) rồi lây lan sang các thiết bị y tế khác cùng mạng. Vì lưu lượng giữa hai thiết bị **cùng một VLAN** đi thẳng qua Access Switch ở Layer 2 mà **không đi lên Core Switch**, Extended ACL gắn trên SVI Core sẽ không thấy và không chặn được $\rightarrow$ bắt buộc phải dùng **Micro-segmentation trên OVS (SDN)** ở Nhóm 4.

---

### NHÓM 3: BẢO MẬT BIÊN & ỨNG DỤNG (PERIMETER & DMZ)

#### 10. Border Router (`U1`) & GRE / IPsec VPN
* **Border Router (`FRR` / `VyOS`):** Bộ định tuyến ngoài cùng kết nối mạng bệnh viện với Internet và các chi nhánh.
* **GRE / IPsec VPN:** Kỹ thuật đóng gói và mã hóa đường hầm qua Internet công cộng để kết nối các chi nhánh (`DBP Branch`, `BHTQ Branch`) về trụ sở chính bệnh viện an toàn.

#### 11. NGFW (Next-Generation Firewall — `OPNsense U3`) & IPS biên
* **Firewall truyền thống vs. NGFW:** Firewall cổ điển chỉ lọc theo IP và Port (Layer 3/4). **NGFW (`OPNsense`)** bổ sung kiểm tra sâu gói tin (**DPI — Deep Packet Inspection**), nhận diện ứng dụng, chia vùng bảo mật (**Zones**: `OUTSIDE`, `INSIDE`, `DMZ`) và tích hợp sẵn **IPS (`Suricata`)** để chặn các cuộc tấn công dựa trên chữ ký (signature-based) ngay tại cửa ngõ bệnh viện.

#### 12. DMZ (`VLAN 210`) & WAF (Web Application Firewall — `ModSecurity` / `OWASP CRS`)
* **DMZ (Demilitarized Zone):** Vùng mạng đệm cô lập vật lý (`SW-DMZ` nối thẳng vào cổng `DMZ` của Firewall `U3`, không nối vào Core), chứa các dịch vụ công khai (`Public Web`, `Public DNS`). Nếu máy chủ DMZ bị xâm nhập, Firewall `U3` vẫn ngăn không cho kẻ tấn công đi vào Data Center (`VLAN 200`).
* **Tại sao có NGFW rồi vẫn cần WAF?** NGFW bảo vệ ở tầng mạng và phiên kết nối, còn **WAF (`Nginx + ModSecurity` với bộ luật `OWASP Core Rule Set`)** đứng ngay trước ứng dụng Web (sau bước giải mã TLS/HTTPS) để phân tích chi tiết giao thức HTTP/HTTPS, chặn các cuộc tấn công vào logic và mã nguồn Web như **SQL Injection (SQLi)**, **Cross-Site Scripting (XSS)** hay các lỗ hổng **OWASP Top 10**.

---

### NHÓM 4: LÕI LUẬN VĂN — SDN & ZERO TRUST ARCHITECTURE (ZTA)

#### 13. SDN (Software-Defined Networking), OpenFlow 1.3 & OVS (Open vSwitch)
* **SDN:** Kiến trúc tách rời **Control Plane** (bộ não quyết định đường đi/chính sách) khỏi **Data Plane** (cơ chế chuyển tiếp gói tin trên Switch), tập trung quyền điều khiển vào **SDN Controller (`OS-Ken` / `Ryu` / `ONOS`)** tại `Server 1`.
* **OpenFlow 1.3 & OVS:** Switch **Open vSwitch (OVS)** chạy trên Linux nhận bảng luật động (**Flow Rules**) từ SDN Controller qua giao thức OpenFlow (cổng `6653`). Khi cần cô lập một máy nhiễm độc, Controller cài trực tiếp một flow rule ưu tiên cao (`priority=50000`, `actions=drop`, kèm thời hạn `hard_timeout=120`) xuống OVS để chặn ngay theo MAC/IP trong vài mili-giây.
* **Lý do dùng Kiến trúc Lai (Cisco Core + OVS Edge/Access):** Cisco `vIOS-L2` trên EVE-NG làm tốt L2/L3/HSRP truyền thống nhưng **không hỗ trợ OpenFlow và lệnh SPAN (`monitor session`)**. Do đó đồ án giữ Cisco Core cho lớp xương sống HSRP và dùng **OVS** tại tầng Phân khu/Access (`BLD-A`, `BLD-B`, `IoMT`) để vừa xuất **SPAN thật**, vừa thực thi **OpenFlow Micro-segmentation & Active IPS**.

#### 14. SPAN (Port Mirroring) vs. Inline
* **SPAN (Mirroring — phương án thiết kế trong ảnh):** OVS nhân bản lưu lượng đi qua Switch và đẩy bản sao sang cổng giám sát của nút Edge AI.
  * *Ưu điểm:* Không làm tăng độ trễ đường dữ liệu chính và không gây mất mạng toàn khu vực nếu nút Edge AI gặp sự cố (fail-open cho luồng hợp lệ).
  * *Nhược điểm:* Luôn có một độ trễ nhỏ (tính bằng `IPS Response Time`) trước khi flow rule chặn được cài xuống PEP, nên một số gói tin đầu tiên có thể đi qua trước khi bị ngắt.
* **Inline:** Đặt nút Edge nằm trực tiếp trên đường đi vật lý của dữ liệu (`Client -> Edge -> Switch`). Cho phép chặn ngay lập tức nhưng phải đánh giá tải throughput, độ trễ và kịch bản lỗi (SPOF).

#### 15. Zero Trust Architecture (ZTA — Chuẩn NIST SP 800-207)
Triết lý cốt lõi: **"Không bao giờ mặc định tin tưởng dù ở bên trong mạng nội bộ — luôn xác thực liên tục" (*Never trust, always verify*)**. Hệ thống vận hành theo vòng lặp **Closed-Loop Active Defense** gồm 3 vai trò logic:
1. **PE (Policy Engine — Bộ não quyết định):** Nằm trên `Server 1`. Tổng hợp bằng chứng từ cảnh báo Edge AI, danh tính thiết bị (FreeRADIUS/PKI) và mức độ tin cậy (Trust Score) để ra quyết định (`ALLOW`, `RATE_LIMIT`, `QUARANTINE`, `RELEASE`). AI chỉ cung cấp bằng chứng, không tự ý thay thế toàn bộ chính sách truy cập.
2. **PA (Policy Administrator — Bộ điều phối thực thi):** Nằm trên `Server 1`. Nhận quyết định từ PE rồi gọi REST API tới SDN Controller (`OS-Ken`) để lập trình hoặc gỡ bỏ luật truy cập trên Switch.
3. **PEP (Policy Enforcement Point — Điểm thực thi chính sách):** Các Switch **OVS** (tại tầng Access/Dist) trực tiếp cho phép hoặc chặn (`DROP`) lưu lượng.
4. **Micro-segmentation (Vi phân đoạn):** Giới hạn quyền truy cập chi tiết theo từng nhóm thiết bị và từng dịch vụ cụ thể, chặn triệt để giao tiếp ngang L2 giữa các thiết bị cùng VLAN (như giữa các thiết bị IoMT trong `VLAN 300`).

---

### NHÓM 5: TRÍ TUỆ NHÂN TẠO & HỌC MÁY LIÊN KẾT (FL-IDS)

#### 16. IDS vs. IPS & Trích xuất đặc trưng luồng (Flow Feature Extraction)
* **IDS (Intrusion Detection System):** Hệ thống phát hiện và sinh cảnh báo xâm nhập.
* **IPS (Intrusion Prevention System):** Hệ thống vừa phát hiện vừa chủ động ngăn chặn lưu lượng độc hại. Khi Edge IDS kết nối khép kín với ZTA PE/PA và OVS OpenFlow thì hình thành hệ thống **Active IPS**.
* **Flow Feature Extraction (`NFStream` / `CICFlowMeter` / `Scapy`):** Gom các gói tin có cùng 5-tuple (`Src IP, Dst IP, Src Port, Dst Port, Protocol`) thành từng **luồng (Flow)** và tính toán các đặc trưng thống kê (tốc độ gói, tổng byte, thời lượng flow, cờ TCP...) khớp hoàn toàn với bộ đặc trưng của tập dữ liệu **Edge-IIoTset / TON_IoT**.

#### 17. Mô hình Deep Learning `CNN + BiLSTM`
* **CNN (Convolutional Neural Network):** Mạng tích chập giúp trích xuất hiệu quả các **mẫu đặc trưng cục bộ (không gian)** giữa các thuộc tính của một luồng mạng.
* **BiLSTM (Bidirectional Long Short-Term Memory):** Mạng hồi quy hai chiều, học tốt **ngữ cảnh tuần tự theo thời gian** của chuỗi lưu lượng (phù hợp phát hiện các cuộc tấn công kéo dài nhiều bước như Port Scan, Botnet, DDoS, Ransomware).
* **Kiến trúc lai `CNN + BiLSTM`:** CNN làm lớp lọc nén đặc trưng tinh gọn rồi đưa vào BiLSTM phân tích chuỗi, đạt độ chính xác cao nhưng vẫn đủ nhẹ để suy luận (inference) ngay tại các nút Edge.

#### 18. Federated Learning (FL), `Flower` & Thuật toán `FedAvg`
* **Tại sao không dùng AI tập trung (Centralized Learning)?** Việc gom toàn bộ lưu lượng thô từ các khu khám bệnh và thiết bị IoMT về một máy chủ trung tâm gây **vi phạm quyền riêng tư dữ liệu bệnh nhân**, tiêu tốn băng thông và tăng độ trễ.
* **Cơ chế Federated Learning (`Flower` framework):**
  1. Dữ liệu thô được **giữ nguyên cục bộ** tại `Edge A`, `Edge B`, `Edge IoMT`.
  2. Mỗi Edge tự huấn luyện mô hình cục bộ (Local Training) trên lưu lượng tại phân khu của mình.
  3. Các Edge **chỉ gửi trọng số mô hình (Model Weights)** qua kênh mã hóa mTLS về `Server 2` (`FL Aggregator`).
  4. `Server 2` chạy thuật toán **`FedAvg` (Federated Averaging)** — lấy trung bình có trọng số (tỉ lệ theo số mẫu huấn luyện của từng Edge) để tạo ra **Global Model** mới rồi phát ngược xuống cho các Edge cập nhật.

#### 19. Non-IID Data & Data/Model Poisoning
* **Non-IID (Non-Independent and Identically Distributed):** Hiện tượng phân phối dữ liệu không đồng nhất giữa các nút biên ngoài thực tế (ví dụ `Edge A/B` chủ yếu gặp lưu lượng máy trạm HTTP/EHR và tấn công Web, còn `Edge IoMT` chủ yếu gặp lưu lượng MQTT/cảm biến và DDoS IoT). Xử lý Non-IID là nội dung đánh giá quan trọng ở Chương 3 và Chương 5.
* **Data / Model Poisoning:** Nguy cơ kẻ tấn công chiếm quyền hoặc giả mạo một nút Edge để gửi trọng số độc hại nhằm làm sai lệch Global Model. Đồ án giảm thiểu rủi ro này bằng **xác thực mTLS qua PKI (`Step-CA`)** trước khi Edge được phép tham gia vòng FL.

---

### NHÓM 6: DANH TÍNH, BẢO MẬT KÊNH TRUYỀN, GIÁM SÁT & ĐO ĐẠC CHƯƠNG 5

#### 20. PKI (`Step-CA`), mTLS & Authenticated Alerts
* **PKI (Public Key Infrastructure):** Hạ tầng quản lý khóa công khai, chịu trách nhiệm cấp phát và thu hồi chứng chỉ số (X.509) cho từng thiết bị và dịch vụ.
* **mTLS (Mutual TLS):** Xác thực TLS **hai chiều** (cả Client và Server đều phải xuất trình chứng chỉ hợp lệ do PKI nội bộ ký).
* **Ứng dụng bảo vệ Control Plane:** Dùng mTLS (kèm JWT ký số) cho 2 kênh quan trọng: (1) `Edge -> Server 1` đảm bảo **Authenticated Alerts** (chống giả mạo cảnh báo làm SDN khóa nhầm máy bác sĩ), và (2) `Edge <-> Server 2` chống thiết bị lạ chen vào vòng huấn luyện FL.

#### 21. FreeRADIUS (AAA / 802.1X) & RBAC (`401` / `403` / `200`)
* **FreeRADIUS:** Máy chủ xác thực tập trung (Authentication, Authorization, Accounting) lưu thông tin danh tính người dùng/thiết bị, hỗ trợ chuẩn **802.1X** và cung cấp ngữ cảnh định danh cho ZTA Policy Engine.
* **RBAC (Role-Based Access Control) & các mã kiểm thử HTTP trên `Server 3`:**
  * `401 Unauthorized`: Chưa đăng nhập hoặc sai thông tin xác thực.
  * `403 Forbidden`: Đăng nhập hợp lệ (ví dụ tài khoản `visitor`) nhưng không đủ quyền truy cập tài nguyên y tế, hoặc đi từ vùng mạng không được phép.
  * `200 OK`: Đúng vai trò hợp lệ (`clinical`) và đi từ đúng vùng mạng cho phép.

#### 22. SIEM (`Wazuh`)
* **SIEM (Security Information and Event Management):** Hệ thống thu thập, đối chiếu và hiển thị nhật ký bảo mật tập trung tại `Server 4 (192.168.200.13)` từ tất cả các lớp (NGFW OPNsense, WAF ModSecurity, Edge FL-IDS, ZTA PE/PA và OVS OpenFlow) trên một màn hình giám sát duy nhất.

#### 23. Năm chỉ số thực nghiệm bắt buộc ở Chương 5 Luận văn
* **`tcpreplay`:** Công cụ phát lại các tệp gói tin tấn công (`.pcap`) vào mạng thử nghiệm để tái lập kịch bản tấn công có kiểm soát và đo đạc lặp lại nhiều lần.
* **Accuracy, Precision, Recall, F1-Score:** Bộ chỉ số đánh giá mô hình FL-IDS so với Centralized Baseline. Trong bài toán phát hiện xâm nhập mất cân bằng dữ liệu, **Precision** (hạn chế báo động giả gây chặn nhầm), **Recall** (không bỏ sót tấn công) và **F1-Score** có ý nghĩa quyết định hơn Accuracy đơn thuần.
* **Convergence (Tốc độ hội tụ):** Số vòng giao tiếp FL (rounds) cần thiết để Global Model đạt hiệu năng ổn định trong cả điều kiện IID và Non-IID.
* **Communication Overhead:** Tổng dung lượng truyền tải (MB/round) để trao đổi trọng số trên mạng điều khiển, dùng để chứng minh FL tiết kiệm băng thông so với gửi dữ liệu thô về trung tâm.
* **Network Latency & IPS Response Time (`T_response`):**
  * **Network Latency:** Độ trễ mạng của người dùng hợp lệ khi chính sách ZTA/OpenFlow đang vận hành.
  * **IPS Response Time (`t3 - t0`):** Tổng thời gian từ thời điểm gói tin tấn công đầu tiên đi vào OVS (`t0`) $\rightarrow$ Edge phát hiện (`t1`) $\rightarrow$ ZTA PE ra quyết định (`t2`) $\rightarrow$ OpenFlow rule được cài đặt và bắt đầu drop trên OVS (`t3`).

---

## PHẦN 3: LỘ TRÌNH 6 BƯỚC & BẢNG ÁNH XẠ CODE TRONG REPO

| Bước | Tên giai đoạn | Thành phần thực hiện chính | Vị trí trong Repo (`hospital-zta-sdn-fl`) |
| :---: | :--- | :--- | :--- |
| **1** | **Nền tảng IaC & Vá bảo mật Core** | 12 VLAN, HSRP Active/Active, STP PVST, ACL `GUEST`/`IOMT`/`OOB`, khóa VTY, tự động hóa `HOSPITAL-SERVERS` | `design/network_spec.yml`, `infra/ansible/playbooks/00..02`, `99_verify_step1.yml`, `scripts/validate_design.py` |
| **2** | **Lõi SDN (OVS) & ZTA Closed-Loop** | Chèn OVS ở Access/Dist, bật SPAN + OpenFlow 1.3, dựng `OS-Ken` + FastAPI ZTA PE/PA (`Server 1`), nâng cấp EHR/PACS (`Server 3`) | `infra/ansible/playbooks/04_ovs_sdn_pep.yml`, `services/sdn_zta/`, `services/hospital_apps/`, `contracts/` |
| **3** | **Vành đai Biên (NGFW + WAF + VPN)** | Dựng `U1` Border (FRR/VyOS + GRE/IPsec), `U3` OPNsense NGFW/Suricata, `SW-DMZ` (`Nginx + ModSecurity` + `CoreDNS`) | `infra/ansible/playbooks/03_perimeter_waf.yml`, `services/dmz_waf/` |
| **4** | **AI & Federated Learning (Song song)** | Tiền xử lý Edge-IIoTset/TON_IoT, train & benchmark `CNN + BiLSTM` (Centralized vs FedAvg Non-IID), đóng gói Flower Server & Edge Agent | `services/fl_engine/` (`Server 2: .200.11` & `Edge A/B/IoMT`) |
| **5** | **Tích hợp Toàn tuyến & PKI/SIEM** | Cấp chứng chỉ mTLS (`Step-CA`), xác thực `FreeRADIUS`, đổ log toàn bộ về `Wazuh SIEM`, nối 3 Edge nhận SPAN thật & test vòng khép kín | `services/security_ops/` (`Server 4: .200.13`), `infra/ansible/playbooks/05_zta_fl_siem.yml` |
| **6** | **Kiểm chứng Open-Source & Đo Chương 5** | Xóa sạch lab test rebuild 100% từ `README.md`, chạy `tcpreplay` đo 5 bộ chỉ số Chương 5 nhiều lần lấy trung bình/độ lệch chuẩn | `Makefile`, `experiments/`, `docs/` |

---

## PHẦN 4: 4 CÂU HỎI HỘI ĐỒNG HAY HỎI & CÁCH TRẢ LỜI CHUẨN

1. **"Phản ứng chặn tấn công (IPS) có phải chờ máy chủ FL tổng hợp xong trọng số không?"**
   * **Trả lời:** **Không.** Luồng phát hiện (Inference) chạy cục bộ ngay tại Edge bằng model hiện tại để báo ZTA/SDN chặn trong thời gian ngắn (`IPS Response Time`). Quá trình huấn luyện và tổng hợp trọng số FL (`FedAvg`) chạy bất đồng bộ ở nền theo chu kỳ để cập nhật nâng cấp độ thông minh của mô hình theo thời gian.

2. **"Tại sao trong kiến trúc lại dùng cả Switch Cisco (`vIOS-L2`) lẫn `Open vSwitch (OVS)`?"**
   * **Trả lời:** Hạ tầng Core bệnh viện đòi hỏi tính sẵn sàng cao với giao thức truyền thống (HSRP Active/Active, STP PVST) được quản trị tập trung bằng Ansible IaC, nhưng image giả lập Cisco `vIOS-L2` trên EVE-NG không hỗ trợ OpenFlow và lệnh SPAN (`monitor session`). Vì vậy nhóm thiết kế **kiến trúc lai**: giữ lõi Core Cisco HSRP ổn định và triển khai lớp **OVS programmable PEP** tại tầng Phân khu/Access để vừa lấy bản sao SPAN thật cho Edge AI, vừa thực thi vi phân đoạn Layer 2 và chặn động qua OpenFlow 1.3.

3. **"Nếu Edge chỉ nhận bản sao qua SPAN thì gói tin tấn công đầu tiên đã đi qua rồi, có gọi là IPS được không?"**
   * **Trả lời:** Đây là mô hình **Near-real-time Active IPS** (phổ biến trong các kiến trúc SDN-based IPS). Ưu điểm là giữ nguyên hiệu năng đường truyền chính và tránh điểm nghẽn đơn (SPOF) khi Edge AI quá tải hoặc bảo trì; đánh đổi là một số gói tin đầu tiên có thể đi qua trong khoảng thời gian phát hiện và cài flow (`T_response = t3 - t0`), thông số này được nhóm đo đạc minh bạch tại Chương 5.

4. **"Giá trị 'Open-Source có thể build lại được' của đồ án thể hiện ở đâu?"**
   * **Trả lời:** Mọi thành phần từ bảng quy hoạch 12 VLAN, HSRP, ACL, cấu hình Switch/OVS, cho tới máy chủ ứng dụng, ZTA/SDN, WAF, FL và SIEM đều được quản lý bằng **Single Source of Truth (`network_spec.yml`) + Ansible + Docker + CI/CD**, tách biệt phần địa chỉ môi trường sang thư mục `inventories/` (`lead_lite`, `member1_local`, `member2_local`, `cloud_full`), cho phép bất kỳ ai clone repo về đều có thể tự động dựng lại và kiểm chứng hệ thống trên cả laptop cá nhân lẫn server cấu hình cao.
