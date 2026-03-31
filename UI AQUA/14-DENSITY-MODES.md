# 14. Density Modes

Tài liệu này mô tả các chế độ mật độ hiển thị nên dùng nếu UI AQUA cần mở rộng.

## 14.1 Mục tiêu
Cho phép cùng một hệ UI có thể:
- đọc thoáng
- đọc chuẩn
- đọc dày

mà không phá cấu trúc thiết kế gốc.

## 14.2 Chế độ Thoáng

### Dùng khi
- demo
- onboarding
- màn có ít dữ liệu
- cấu hình/form

### Đặc điểm
- padding lớn hơn
- ít cột hơn
- card cao hơn
- text thoáng hơn

## 14.3 Chế độ Chuẩn

### Đây là mặc định
- cân bằng đọc và mật độ
- phù hợp hầu hết tab AQUA

### Đặc điểm
- spacing vừa
- card cao vừa
- summary rõ
- badge đủ lớn để đọc

## 14.4 Chế độ Dày

### Dùng khi
- inventory lớn
- tab Nhiệm Vụ
- tab Skill Forge
- tab logs

### Đặc điểm
- nhiều cột hơn
- card thấp hơn
- text nhỏ hơn một nấc
- metadata được rút gọn

## 14.5 Quy tắc khi đổi mode
- không đổi màu semantic
- không đổi hierarchy title/subtext
- không bỏ badge quan trọng
- chỉ đổi:
  - số cột
  - padding
  - gap
  - clamp text

## 14.6 Mapping thực tế

### Thoáng
- 2-3 card / hàng
- padding 16-18

### Chuẩn
- 3-4 card / hàng
- padding 14-16

### Dày
- 4-6 card / hàng
- padding 10-14

## 14.7 Không được làm
- giảm density bằng cách giấu mất dữ liệu quan trọng
- tăng density đến mức card vỡ layout
- chỉ tăng số cột mà không giảm content complexity
