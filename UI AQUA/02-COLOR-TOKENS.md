# 02. Color Tokens

## 2.1 Core palette
Nguồn màu gốc đang dùng trong AQUA:

- `Primary`: `oklch(74.703% 0.158 39.947)`
- `Secondary`: `oklch(72.537% 0.177 2.72)`
- `Accent`: `oklch(71.294% 0.166 299.844)`
- `Neutral`: `oklch(26% 0.019 237.69)`
- `Base 100`: `oklch(22% 0.019 237.69)`
- `Base 200`: `oklch(20% 0.019 237.69)`
- `Base 300`: `oklch(18% 0.019 237.69)`
- `Info`: `oklch(85.559% 0.085 206.015)`
- `Success`: `oklch(85.56% 0.085 144.778)`
- `Warning`: `oklch(85.569% 0.084 74.427)`
- `Error`: `oklch(85.511% 0.078 16.886)`

## 2.2 Semantic mapping
- `Primary`: điểm nhấn chính, name quan trọng, active emphasis
- `Secondary`: nhóm cảnh báo mềm, reminder, trạng thái phụ
- `Accent`: Skill Forge, trạng thái trung cấp, điểm nhấn tím
- `Neutral`: nền chip, border, lớp trung tính
- `Info`: dashboard, system info, route, gateway, timer tone lạnh
- `Success`: trạng thái ổn, knowledge, backup an toàn
- `Warning`: ưu tiên cao, theo dõi, cảnh báo, attention state
- `Error`: lỗi, expired, failed, destructive action

## 2.3 Text color roles
- `--text-strong`: heading, title, primary content
- `--text-soft`: text hỗ trợ nhưng vẫn cần đọc rõ
- `--text-muted`: label nhỏ, mô tả, caption

## 2.4 Surface rules
Luôn dùng dark surfaces theo thứ tự:
- `base background`
- `panel background`
- `card background`
- `chip background`

Không dùng màu thương hiệu phủ thẳng lên toàn bộ panel lớn.
Màu thương hiệu chỉ nên dùng:
- active tab
- badge trạng thái
- accent line
- subtle glow
- tone card theo nhóm

## 2.5 Tone bucket
AQUA dùng bucket màu nhẹ cho từng nhóm:
- `sky`: mission, process, cpu, ram, disk, runtime
- `cyan`: timer, gateway, openclaw, tunnel, route
- `emerald`: knowledge, memory, soul, learning
- `violet`: skill, script, automation, forge
- `rose`: reminder, report, proposal
- `amber`: warning, restart, overdue, critical
- `indigo`: git, package, repo
- `lime`: backup, restore, archive
- `slate`: neutral, token, auth, misc

## 2.6 Độ mạnh màu
- Tone chỉ vừa đủ để phân nhóm.
- Màu mạnh nhất chỉ nên dùng cho:
  - active tab
  - primary button
  - critical badge
  - theo dõi/favorite

## 2.7 Quy tắc gradient
- Gradient phải nhẹ.
- Gradient không được phá khả năng đọc.
- Không dùng line gradient mỏng nếu làm card khó nhìn.
- Gradient nên ở:
  - nền tab active
  - nền button primary
  - nền meter/progress
  - nền card tone nhẹ

## 2.8 Contrast
Mỗi màn hình phải đảm bảo:
- card nổi hơn nền
- badge nổi hơn card
- name nổi hơn metadata
- button nổi hơn text thường

Nếu nhìn nhanh mà card và panel gần như cùng màu, coi như fail.
