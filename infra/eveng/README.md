# Hạ tầng EVE-NG Topology & Day-0 Bootstrap (`infra/eveng/`)

Thư mục này chứa file topology `.unl` xuất từ EVE-NG và cấu hình Bootstrap tối thiểu để Ansible điều khiển thiết bị qua mạng OOB (`VLAN 999`).

## 1. File cần bổ sung từ Member 1
- Export bài lab EVE-NG hiện tại của bạn thành file `hospital_step1.unl` (sau Bước 2 sẽ có thêm `hospital_lite.unl` và `hospital_full.unl`) và đặt vào thư mục này.
- Lưu ý đồng bộ đúng tên image trên mọi máy:
  - Cisco Switch: `vios_l2-adventerprisek9-m` (`15.2(4.0.55)E`)
  - Linux Server / OVS: Ubuntu Server LTS `24.04`

## 2. Bảng nối dây Bước 1 trên EVE-NG

| Từ Thiết bị (Cổng) | $\longleftrightarrow$ | Tới Thiết bị (Cổng) | Ghi chú |
| :--- | :---: | :--- | :--- |
| **Cả 7 Switch (`Gi0/0`)** | $\longleftrightarrow$ | **`Management(Cloud0)`** (hoặc `Cloud1` trên Cloud) | OOB Management (VLAN 999) |
| `SW-CORE-01` (`Gi0/2`) | $\longleftrightarrow$ | `SW-CORE-02` (`Gi0/2`) | 802.1Q Trunk Interlink |
| `SW-CORE-01` (`Gi0/3`) / `02` (`Gi0/3`) | $\longleftrightarrow$ | `SW-BLD-A` (`Gi0/1`, `Gi0/2`) | 802.1Q Trunk Tòa A |
| `SW-CORE-01` (`Gi1/0`) / `02` (`Gi1/0`) | $\longleftrightarrow$ | `SW-BLD-B` (`Gi0/1`, `Gi0/2`) | 802.1Q Trunk Tòa B |
| `SW-CORE-01` (`Gi1/1`) / `02` (`Gi1/1`) | $\longleftrightarrow$ | `SW-IOMT` (`Gi0/1`, `Gi0/2`) | 802.1Q Trunk IoMT |
| `SW-CORE-01` (`Gi1/2`) / `02` (`Gi1/2`) | $\longleftrightarrow$ | `SW-DC` (`Gi0/1`, `Gi0/2`) | 802.1Q Trunk Data Center |
| `Cloud1` (`VMnet2`) | $\longleftrightarrow$ | `SW-DC` (`Gi1/1`) | Access `VLAN 200` nối tới `ens33` của `HOSPITAL-SERVERS` |

## 3. Cấu hình Bootstrap Day-0 (Chỉ dán 1 lần khi tạo Switch trắng mới)

Đổi `hostname` và IP `Gi0/0` khớp với file `hosts.ini` của profile bạn chọn (`.51` $\rightarrow$ `.57`):

```cisco
enable
configure terminal
hostname SW-CORE-01
ip domain-name hospital.local
username admin privilege 15 secret eve
enable secret eve
crypto key generate rsa modulus 2048
ip ssh version 2
!
interface GigabitEthernet0/0
 description OOB_MGMT_VLAN_999_TO_ANSIBLE
 no switchport
 ip address 192.168.139.51 255.255.255.0
 no shutdown
 exit
!
line vty 0 15
 transport input ssh
 login local
 exec-timeout 30 0
end
write memory
copy running-config flash:bootstrap.cfg
```
