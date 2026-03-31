# 12. Content Language

Tài liệu này chuẩn hoá cách viết nội dung tiếng Việt trong UI AQUA.

## 12.1 Giọng điệu
- ngắn
- rõ
- vận hành
- không văn vẻ
- không mơ hồ

## 12.2 Tên tab
Tên tab nên:
- là danh từ hoặc cụm danh từ rõ
- ngắn
- có thể đi với icon

Ví dụ tốt:
- `Tổng Quan`
- `Nhiệm Vụ`
- `Skill Forge`
- `Nhắc Việc`
- `Tàng Thư Các`
- `Sao Lưu`

## 12.3 Label
Label nên có cấu trúc:
- `Danh mục: Giá trị`

Ví dụ:
- `Trạng thái: Đang chạy`
- `Ưu tiên: Rất cao`
- `Loại: Timer`
- `Nguồn: Systemd user`

## 12.4 Tên section
Tên section nên:
- mô tả đúng loại dữ liệu
- tránh chung chung

Ví dụ:
- `System services quan trọng`
- `Nhóm Telegram đang dùng thật`
- `Log OpenClaw / Action gần đây`

## 12.5 Text mô tả ngắn
Mô tả nên:
- chỉ 1 câu
- nêu mục đích phần đó
- không giải thích lan man

Ví dụ:
- `Dạng card để đọc nhanh từng nhiệm vụ, ưu tiên, tài nguyên và timer.`

## 12.6 Trạng thái
Chuẩn từ:
- `Đang chạy`
- `Không chạy`
- `Đang bật`
- `Đang tắt`
- `Lỗi`
- `Cảnh báo`
- `Hoàn tất`
- `Chưa xài`

## 12.7 Từ cần tránh
- quá kỹ thuật khi không cần
- mơ hồ
- cụt nghĩa

Ví dụ nên tránh:
- `High`
- `Done`
- `Live`
- `Warning`

Nếu dùng thuật ngữ kỹ thuật, phải có ngữ cảnh.

## 12.8 Mô tả path, unit, id
- path: có thể giữ nguyên kỹ thuật
- unit: giữ nguyên tên systemd
- id: giữ nguyên kỹ thuật
- nhưng label xung quanh phải là tiếng Việt

Ví dụ:
- `Unit: openclaw-watchdog.timer`
- `Đường dẫn: /home/ubuntu/...`

## 12.9 Emoji / icon text
Emoji dùng để định hướng, không thay nội dung.

Ví dụ tốt:
- `🧠 Tàng Thư Các`
- `🚀 Nhiệm Vụ`

Ví dụ không tốt:
- chỉ có icon mà không có text

## 12.10 Prompt ngôn ngữ cho AI
Khi yêu cầu AI sinh UI mới, nên thêm:

```md
Dùng tiếng Việt ngắn, rõ, giàu ngữ cảnh vận hành. Badge và label phải tránh mơ hồ. Ưu tiên cấu trúc “Danh mục: Giá trị”.
```
