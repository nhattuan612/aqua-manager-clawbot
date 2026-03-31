# 09. Component Recipes

Tài liệu này mô tả cách dựng từng component chuẩn trong hệ UI AQUA.

## 9.1 Tab

### Dùng khi
- chuyển giữa các miền chức năng lớn
- mỗi tab là một vùng dữ liệu độc lập

### Không dùng khi
- chỉ là filter nhỏ trong cùng một bảng
- chỉ là toggle 2 trạng thái đơn giản

### Cấu trúc
- icon
- tên tab
- active state rõ
- hover state rõ

### Chuẩn AQUA
- tab đặt ngang
- active tab nổi hơn hẳn
- active tab có nền mạnh hơn và line nhấn
- tab quan trọng hơn có thể được ưu tiên thị giác

### Lỗi thường gặp
- tab thường và tab active quá giống nhau
- dùng quá nhiều tab khiến hàng tab rối
- tab không gợi đúng ý nghĩa nội dung bên trong

## 9.2 Panel

### Dùng khi
- tạo vùng nội dung chính của mỗi tab
- chứa section title, summary, controls, body

### Cấu trúc
- `panel-head`
- summary hoặc controls
- content body

### Chuẩn AQUA
- panel không cần quá phô viền
- panel là shell nhẹ, card bên trong mới là lớp đọc chính

### Lỗi thường gặp
- panel nặng hơn card
- panel và card cùng màu, mất phân tầng

## 9.3 Dense Stat

### Dùng khi
- hiển thị KPI đầu tab
- tổng số, tổng tải, tổng trạng thái

### Cấu trúc
- label
- value
- sub text

### Chuẩn AQUA
- label nhỏ uppercase nhẹ
- value lớn, sáng, đậm
- sub text ngắn, dịu

### Không dùng cho
- nội dung cần nhiều metadata
- mô tả dài

## 9.4 Dense Card

### Dùng khi
- mỗi object có nhiều metadata
- user cần quét nhiều object cùng lúc

### Cấu trúc chuẩn
1. title
2. subtitle
3. status/action row
4. detail grid
5. tag row
6. action row

### Chuẩn AQUA
- card title sáng và nổi
- metadata phụ nhỏ hơn
- text dài bị cắt hợp lý
- badge semantic rõ nghĩa

### Khi cần chia card
- object lớn, nhiều text -> card rộng hơn, ít cột hơn
- object nhỏ, nhiều item -> card nhỏ, nhiều cột hơn

## 9.5 Mission Card

### Nội dung bắt buộc
- tên
- source
- loại
- trạng thái
- ưu tiên
- unit hoặc script

### Nếu là process
- uptime
- CPU
- RAM
- restart

### Nếu là timer
- next run
- last run
- triggers

### Nếu là service
- active state
- unit file state
- triggered by nếu có

## 9.6 Summary Strip

### Dùng khi
- cần chip count nhanh theo nhóm
- cần hiển thị phạm vi đang xem

### Component
- `group-strip`
- `group-chip`

### Không dùng khi
- dữ liệu phức tạp hơn 1 dòng ngắn

## 9.7 Badge

### Dùng cho
- trạng thái
- mức ưu tiên
- cài đặt
- nguồn
- loại

### Quy tắc
- badge phải ngắn
- badge phải semantic
- badge nên có prefix rõ nếu có nguy cơ nhập nhằng

## 9.8 Button

### Loại
- `btn`
- `btn-primary`
- `btn-danger`
- `mini-btn`
- `mini-primary`
- `mini-danger`

### Quy tắc
- primary chỉ 1-2 hành động chính mỗi vùng
- danger không được dùng cho hành động an toàn
- mini button chỉ cho card-level action

## 9.9 Table Shell

### Dùng khi
- người dùng cần so sánh theo cột
- có nhiều row, ít metadata phức tạp

### Không dùng khi
- mỗi hàng thực ra là một object giàu ngữ cảnh

### Chuẩn
- header sticky nếu cần
- hover nhẹ
- spacing đều
- text phụ không được lấn át dữ liệu chính

## 9.10 Log Row

### Dùng khi
- cần xem nhiều nguồn log cùng lúc
- summary quan trọng hơn raw log

### Cấu trúc
- summary ngang
- details body mở rộng

### Chuẩn AQUA
- mặc định đọc được summary
- raw log mở khi cần
- font mono nhỏ

## 9.11 Command Box

### Dùng khi
- hiển thị lệnh shell
- hiển thị URL tokenized
- hiển thị helper command

### Chuẩn
- mono
- xuống dòng đẹp
- có nền riêng
- không nhét quá nhiều prose vào trong

## 9.12 Modal

### Dùng khi
- xem JSON
- xem code
- xem nội dung đầy đủ

### Không dùng khi
- dữ liệu cần so sánh song song nhiều item

### Chuẩn
- title rõ
- body scroll độc lập
- không quá nhiều action
