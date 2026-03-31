# 06. States And Semantics

## 6.1 Trạng thái chuẩn
Phải chuẩn hoá mọi UI theo các trạng thái này:
- `Đang chạy`
- `Đang khởi động`
- `Đang dừng`
- `Không chạy`
- `Đang bật`
- `Đang tắt`
- `Lỗi`
- `Cảnh báo`
- `Hoàn tất`
- `Hết hạn`
- `Chưa xài`

## 6.2 Ưu tiên chuẩn
- `Rất cao`
- `Cao`
- `Vừa`
- `Thấp`
- `Thường`

## 6.3 Ý nghĩa màu
- xanh/teal: đang hoạt động, ổn
- vàng/cam: cần chú ý
- đỏ/hồng: lỗi, expired, destructive
- tím: đối tượng vận hành / skill / action trung tâm
- slate: trung tính / metadata

## 6.4 Gắn ngữ nghĩa rõ
Mọi badge cần cố gắng gắn prefix:
- `Trạng thái:`
- `Ưu tiên:`
- `Nguồn:`
- `Loại:`
- `Cài đặt:`
- `Tiến độ:`
- `Mức gấp:`
- `File unit:`
- `Load:`

## 6.5 Không nhập nhằng
Không ghi:
- `Rất cao`
- `Đang chạy`
- `Thấp`

nếu thiếu ngữ cảnh.

## 6.6 Active vs enabled
Với systemd/timer/service cần tách rõ:
- `ActiveState`: hiện có đang chạy hay đang wait
- `UnitFileState`: có đang enabled/disabled trong systemd không

UI phải thể hiện được cả hai, không gộp làm một.

## 6.7 Theo dõi / watch
Với đối tượng được user quan tâm:
- có thể đánh dấu sao
- có thể lọc riêng
- card được nhấn nhẹ hơn bình thường

## 6.8 Tone theo loại nội dung
Phải nhất quán:
- task/process/timer -> sky/cyan
- reminder/report -> rose
- skill/script -> violet
- knowledge -> emerald
- backup -> lime
- git -> indigo
- auth/token -> slate

## 6.9 Màu không được đánh lừa
Ví dụ:
- trạng thái lỗi không được dùng tone quá giống trạng thái ổn
- button xoá không được nhìn giống button xem JSON
- active tab không được giống tab thường
