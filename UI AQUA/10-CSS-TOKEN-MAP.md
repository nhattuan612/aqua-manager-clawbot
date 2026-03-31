# 10. CSS Token Map

Tài liệu này map từ khái niệm thiết kế sang token/class để AI hoặc người phát triển triển khai nhanh hơn.

## 10.1 Core tokens

### Color tokens
- `--primary`: nhấn chính
- `--secondary`: nhấn phụ, reminder family
- `--accent`: tím vận hành / skill
- `--neutral`: nền trung tính
- `--base-100`, `--base-200`, `--base-300`: 3 tầng nền tối
- `--info`, `--success`, `--warning`, `--error`: semantic state

### Text tokens
- `--text-strong`: title
- `--text-soft`: body đọc thường
- `--text-muted`: label/caption

### Surface tokens
- `--panel-bg`
- `--card-bg`
- `--chip-bg`
- `--line`
- `--line-soft`

## 10.2 Layout classes
- `.page`: container chính
- `.topbar`: header trên cùng
- `.toolbar`: search + global actions
- `.tabs.top-tabs`: tab bar ngang
- `.panel`: shell nội dung tab
- `.panel-head`: title + subtitle + actions

## 10.3 Summary classes
- `.dense-grid`: lưới summary
- `.dense-stat`: khối KPI
- `.group-strip`: hàng chip
- `.group-chip`: chip tổng hợp nhóm

## 10.4 Card classes
- `.card-grid`
- `.card-grid-tight`
- `.card-grid-six`
- `.dense-card`
- `.card-top`
- `.card-title`
- `.card-sub`
- `.tag-row`
- `.actions`

## 10.5 Form and controls
- `.btn`
- `.btn-primary`
- `.btn-danger`
- `.mini-btn`
- `.mini-primary`
- `.mini-danger`
- `.search`
- `.control-select`
- `.restore-input`

## 10.6 Metadata classes
- `.field-row`
- `.field-col`
- `.field-label`
- `.field-value`
- `.meta-box`
- `.mono`
- `.truncate-1`
- `.truncate-2`

## 10.7 State classes
- `.b-status-online`
- `.b-status-warning`
- `.b-status-expired`
- `.b-priority-critical`
- `.b-priority-high`
- `.b-priority-medium`
- `.b-priority-low`
- `.b-kind`

## 10.8 Tone classes
- `.tone-sky`
- `.tone-cyan`
- `.tone-emerald`
- `.tone-violet`
- `.tone-rose`
- `.tone-amber`
- `.tone-indigo`
- `.tone-lime`
- `.tone-slate`

## 10.9 Dynamic mapping rules

### Theo nhóm
- task/process/system -> `tone-sky`
- timer/gateway/openclaw -> `tone-cyan`
- knowledge -> `tone-emerald`
- skill/script -> `tone-violet`
- reminder -> `tone-rose`
- warning/critical -> `tone-amber`
- git/package -> `tone-indigo`
- backup -> `tone-lime`
- neutral/auth -> `tone-slate`

### Theo trạng thái
- running/active/waiting -> `b-status-online`
- pending/warning -> `b-status-warning`
- failed/error/expired -> `b-status-expired`

### Theo ưu tiên
- critical -> `b-priority-critical`
- high -> `b-priority-high`
- medium -> `b-priority-medium`
- low/normal -> `b-priority-low`

## 10.10 Khi AI chọn class

Nếu không chắc:
1. chọn lớp semantic trước
2. chọn tone nhóm sau
3. chỉ thêm custom style nếu class có sẵn không đủ

Không được tạo class mới tràn lan nếu class cũ đủ dùng.
