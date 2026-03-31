# 07. AI Implementation Rules

Tài liệu này dành riêng cho AI agent hoặc model khác khi phải tạo UI mới theo chuẩn AQUA.

## 7.1 Nguồn chuẩn
Luôn đọc trước:
- `UI AQUA/README.md`
- `UI AQUA/02-COLOR-TOKENS.md`
- `UI AQUA/05-COMPONENTS.md`

## 7.2 Khi tạo UI mới
AI phải giữ:
- dark theme
- hierarchy rõ
- card-first cho object data
- badge semantic rõ nghĩa
- màu phân nhóm vừa đủ
- tên nổi bật hơn metadata
- mật độ thông tin cao nhưng không vỡ

## 7.3 Không được tự ý
- chuyển sang theme sáng
- thay font sang system default
- dùng màu ngẫu nhiên không map từ palette AQUA
- tăng bo góc quá nhiều
- dùng shadow/glow quá mạnh
- biến UI vận hành thành landing page

## 7.4 Nếu tạo tab mới
Tab mới phải có:
- icon
- tên tiếng Việt rõ nghĩa
- active state riêng
- summary block
- group strip hoặc control strip nếu cần
- card/table đúng loại dữ liệu

## 7.5 Nếu tạo card mới
Card mới phải có:
- title
- sub text
- state/action row
- content grid
- tag row hoặc action row nếu cần

Card không được:
- nhồi text dài không cắt
- có quá nhiều cột siêu nhỏ
- để label mơ hồ

## 7.6 Nếu tạo màn giám sát
Ưu tiên:
- dense-stat ở đầu
- chip count theo nhóm
- filter/sort rõ
- card theo object
- log theo hàng ngang mở rộng

## 7.7 Nếu tạo màn cấu hình
Ưu tiên:
- field-label rõ
- input shell đồng bộ
- action chính là primary
- action nguy hiểm là danger
- có giải thích ngắn ở đầu panel

## 7.8 Nếu tạo giao diện danh sách dài
Chọn giữa card và table như sau:
- object giàu metadata -> card
- so sánh cột -> table
- log/event -> details row

## 7.9 Kiểm tra trước khi bàn giao
AI phải tự hỏi:
- card có nổi hơn nền không?
- active state có rõ không?
- tên có bị badge che không?
- text dài có làm vỡ card không?
- mobile có co hợp lý không?
- màu có semantic hay chỉ trang trí?

## 7.10 Câu prompt chuẩn cho AI khác
Có thể dùng prompt mẫu sau:

```md
Thiết kế UI mới theo chuẩn UI AQUA.
Giữ dark operational dashboard style, dùng font Inter + JetBrains Mono, card-first layout, badge semantic rõ nghĩa, title sáng và nổi hơn metadata, tone màu phân nhóm nhẹ, active state rõ, không landing-page hóa giao diện. Ưu tiên readability, information density, hierarchy, và consistency với AQUA Manager ClawBot.
```
