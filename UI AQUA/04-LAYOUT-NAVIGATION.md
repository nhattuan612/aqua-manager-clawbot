# 04. Layout And Navigation

## 4.1 Page shell
Cấu trúc trang chuẩn:
1. `Topbar`
2. `Toolbar`
3. `Tab bar`
4. `Current panel`
5. `Group sections`
6. `Cards / table / logs / detail`

## 4.2 Container
Trang không nên full ngang vô hạn.
Ưu tiên:
- container rộng nhưng có khoảng thở hai bên
- desktop lớn vẫn phải có nhịp nhìn rõ

## 4.3 Topbar
Topbar chứa:
- brand
- environment / host / time
- global action nhẹ nếu cần

Không nhồi quá nhiều control vào topbar.

## 4.4 Toolbar
Toolbar chứa:
- search
- reload
- action nhanh
- helper command

Toolbar phải là một shell riêng, nhìn ra ngay nó là control zone.

## 4.5 Tab bar
Tab của AQUA:
- là horizontal navigation
- tab active phải nổi rõ hơn các tab khác
- tab ít dùng có thể lùi nhẹ, nhưng vẫn cùng hệ

Tab ưu tiên nên ở trước:
- Tổng Quan
- Nhiệm Vụ
- Skill Forge
- Nhắc Việc

Tab thiên về kỹ thuật hoặc ít dùng hơn ra sau:
- Tàng Thư Các
- Gói Github
- Sao Lưu
- Khoá/API
- Quyền Telegram
- Cổng OpenClaw

## 4.6 Group section
Mỗi nhóm nội dung lớn nên đi trong:
- `details.group-section`
- có header nhóm
- có count
- có collapse/expand

Nguyên tắc:
- nhóm giúp giảm rối
- nhóm không được che mất dữ liệu chính

## 4.7 Grid rules
Grid hiện tại được dùng theo loại nội dung:
- `card-grid`: card chuẩn
- `card-grid-tight`: card nhỏ hơn
- `card-grid-six`: dense card kiểu skill

Khi mở rộng UI mới:
- dữ liệu dày -> card nhỏ hơn, nhiều cột hơn
- dữ liệu quan trọng, cần đọc sâu -> card to hơn, ít cột hơn

## 4.8 Responsive logic
Không giữ cố định 1 số cột cho mọi màn hình.
Ưu tiên co dần:
- desktop lớn: nhiều cột
- laptop: bớt cột
- tablet: 2 cột
- mobile: 1 cột

## 4.9 Modal
Modal dùng cho:
- code
- json
- log
- xem nội dung đầy đủ

Không dùng modal cho dữ liệu mà người dùng cần xem liên tục.

## 4.10 Scroll
- Bảng dài: scroll ngang có kiểm soát
- Code/log: scroll riêng trong box
- Không để toàn page vỡ layout vì một nội dung dài
