# UI AQUA

Thư mục này là bộ chuẩn giao diện của `AQUA Manager ClawBot`.

Mục tiêu:
- Chuẩn hoá toàn bộ ngôn ngữ thiết kế hiện tại của AQUA.
- Giúp người đọc, AI agent, và các model khác có thể dựng UI mới nhưng vẫn giữ đúng tinh thần hiện tại.
- Làm tài liệu nguồn để mở rộng dashboard hoặc tạo hệ UI mới cùng phong cách.

Triết lý chính của UI AQUA:
- Dark dashboard trước, không phải marketing page.
- Mật độ thông tin cao nhưng vẫn đọc nhanh.
- Màu sắc có vai trò phân loại và định hướng, không để trang trí thừa.
- Card và panel phải đủ tương phản với nền.
- Tên chính luôn nổi bật, thông tin phụ nhỏ hơn và lùi lại.
- Trạng thái, mức độ quan trọng, loại đối tượng phải nhìn ra bằng màu và badge.
- Ưu tiên vận hành, giám sát, đọc nhanh, lọc nhanh, quét nhanh.

Thứ tự đọc khuyến nghị:
1. `01-FOUNDATION.md`
2. `02-COLOR-TOKENS.md`
3. `03-TYPOGRAPHY-SPACING.md`
4. `04-LAYOUT-NAVIGATION.md`
5. `05-COMPONENTS.md`
6. `06-STATES-SEMANTICS.md`
7. `07-AI-IMPLEMENTATION-RULES.md`
8. `08-UI-REVIEW-CHECKLIST.md`

Quy tắc quan trọng:
- Nếu phải chọn giữa “đẹp” và “rõ để vận hành”, chọn vế thứ hai.
- Không tự ý đổi theme sang sáng.
- Không làm card, tab, badge giống màu nhau đến mức mất phân tầng.
- Không dùng bo góc lớn nếu không có lý do.
- Không biến UI AQUA thành landing page bóng bẩy thiếu chiều sâu vận hành.
