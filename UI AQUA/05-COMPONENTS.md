# 05. Components

## 5.1 Button
Loại button chuẩn:
- `btn`: hành động thường
- `btn-primary`: hành động chính
- `btn-danger`: hành động nguy hiểm
- `mini-btn`: hành động phụ trong card
- `mini-primary`
- `mini-danger`

Quy tắc:
- primary chỉ dùng cho action chính
- danger chỉ dùng cho delete/restore/destructive
- mini button không được trông mạnh hơn nút chính

## 5.2 Badge / Chip
Badge dùng cho:
- trạng thái
- ưu tiên
- phân loại
- metadata ngắn

Chip dùng cho:
- group summary
- strip filter
- contextual notes

Không dùng badge cho câu dài.

## 5.3 Dense stat
`dense-stat` là component KPI:
- label nhỏ
- value nổi
- sub text ngắn

Dùng ở:
- summary đầu tab
- quick metrics
- total count

## 5.4 Dense card
`dense-card` là component chủ lực của AQUA.

Cấu trúc khuyến nghị:
1. `card-top`
2. `name`
3. `sub`
4. `status/actions`
5. `detail grid`
6. `tag row`
7. `actions`

Card phải:
- gói gọn
- dễ quét
- có hierarchy rõ
- không nhồi quá nhiều block cao

## 5.5 Mission card
Card nhiệm vụ cần có:
- tên
- loại
- nguồn
- trạng thái
- ưu tiên
- path hoặc unit file
- timer/service relation nếu có
- JSON hoặc detail action

Nếu là process:
- có uptime, CPU, RAM, restart

Nếu là timer:
- có next run, last run, triggers

## 5.6 Table shell
Table chỉ dùng khi:
- dữ liệu cần so sánh dạng cột thật sự
- row count cao
- thao tác đọc theo cột quan trọng hơn đọc theo object

Nếu mỗi hàng có quá nhiều metadata kiểu object, nên chuyển sang card.

## 5.7 Log row
Log dùng `details.log-row`:
- summary ngang để quét
- body mở rộng khi cần

Đây là pattern chuẩn cho log/terminal summary.

## 5.8 Route item / cmd box
`route-item`: mô tả endpoint / route / helper route
`cmd-box`: lệnh shell / tunnel / URL tokenized / snippet kỹ thuật

`cmd-box` phải dùng mono.

## 5.9 Input
Input chuẩn:
- nền tối
- viền rõ
- radius vừa
- focus ring nhẹ bằng màu semantic

## 5.10 Summary strip
`group-strip` và `group-chip` dùng để:
- đọc tổng quan nhóm
- count nhanh
- highlight phạm vi

Không dùng nó để thay thế panel chính.
