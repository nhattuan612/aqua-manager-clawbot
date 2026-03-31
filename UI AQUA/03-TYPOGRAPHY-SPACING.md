# 03. Typography And Spacing

## 3.1 Font stack
Chuẩn AQUA hiện tại:
- `Inter`: text chính
- `JetBrains Mono`: code, path, id, command, terminal, kỹ thuật

Không thay bằng:
- Arial
- Roboto
- system default

trừ khi có ràng buộc kỹ thuật rõ ràng.

## 3.2 Font hierarchy
Các cấp chữ nên giữ logic này:
- `Page title`: 22px, 800
- `Section title`: 24px trong shell hiện đại, 700-800
- `Card title`: 12-13px, 800
- `Value lớn`: 14px+
- `Body text`: 11-13px
- `Sub text`: 10-12px
- `Label nhỏ`: 9.5-10px uppercase nhẹ
- `Mono metadata`: 10.5-11px

## 3.3 Quy tắc cho Name
Tên chính của card:
- luôn là một dòng ưu tiên riêng nếu có nguy cơ bị badge che
- màu sáng hơn phần còn lại
- đậm hơn phần còn lại
- không để label chen cùng dòng nếu gây mất tên

## 3.4 Label
Label phải:
- ngắn
- rõ nghĩa
- có ngữ cảnh

Ví dụ đúng:
- `Trạng thái: Đang chạy`
- `Ưu tiên: Rất cao`
- `Tiến độ: Hoàn tất`
- `Mức gấp: Thấp`

Ví dụ sai:
- `Đang chạy`
- `Rất cao`
- `Hoàn tất`
- `Thấp`

## 3.5 Spacing scale
Scale spacing nên xoay quanh:
- `4px`
- `6px`
- `8px`
- `10px`
- `12px`
- `14px`
- `16px`

Không nhảy spacing vô cớ.

## 3.6 Padding chuẩn
- `Chip / badge`: 4x8 hoặc 4x10
- `Mini button`: 3x6 đến 6x10
- `Button`: khoảng 10x14
- `Dense card`: khoảng 14-16
- `Panel`: khoảng 14-18
- `Toolbar`: khoảng 12-16

## 3.7 Margin chuẩn
- giữa section: 10-20
- giữa title và nội dung: 8-14
- giữa card trong grid: 8-14
- giữa badge trong tag row: 4-8

## 3.8 Quy tắc text dài
- Path dài: luôn truncate hoặc shortPath
- Mô tả dài: tối đa 2 dòng, cần thì bấm xem chi tiết
- JSON/log/code: chuyển sang modal/box riêng
- Không để text raw làm vỡ chiều ngang card

## 3.9 Corner radius
Chuẩn ưu tiên:
- chip/button nhỏ: 12-14 hoặc pill
- card/panel: 14-20
- modal: 8-20 tuỳ shell

Không dùng bo góc quá lớn nếu toàn bộ hệ còn lại đang gọn.
