# 15. Example Wireframes

Tài liệu này cung cấp wireframe chữ để AI hoặc dev dựng màn hình mới theo chuẩn AQUA mà không phải đoán layout.

## 15.1 Overview Page

```text
┌──────────────────────────────────────────────────────────────┐
│ Topbar: Brand / Host / Time / Global Action                 │
├──────────────────────────────────────────────────────────────┤
│ Toolbar: Search | Reload | Quick Action                     │
├──────────────────────────────────────────────────────────────┤
│ Tabs: Tổng Quan | Nhiệm Vụ | Skill Forge | ...              │
├──────────────────────────────────────────────────────────────┤
│ Section Head: Title + Subtitle + Action                     │
├──────────────────────────────────────────────────────────────┤
│ Dense Stat Grid                                             │
│ [CPU] [RAM] [Disk] [Uptime] [Tasks] [Warnings] [Backup]     │
├──────────────────────────────────────────────────────────────┤
│ Group Chips                                                 │
│ [PM2] [Service user] [Timer user] [System service] ...      │
├──────────────────────────────────────────────────────────────┤
│ Alert Cards                                                 │
│ [Tiến trình cần chú ý] [Reminder quá hạn] [Backup điểm yếu] │
├──────────────────────────────────────────────────────────────┤
│ Log Rows                                                    │
│ > bot                  Hoạt động      ...                   │
│ > assistant_scheduler  Có lỗi         ...                   │
└──────────────────────────────────────────────────────────────┘
```

## 15.2 Inventory Page

```text
┌──────────────────────────────────────────────────────────────┐
│ Section Head                                                │
├──────────────────────────────────────────────────────────────┤
│ Dense Stat Grid                                             │
│ [Tổng] [Rất cao] [Timer] [Đang chạy] [Không chạy] [Watch]   │
├──────────────────────────────────────────────────────────────┤
│ Group Chips / Summary Strip                                 │
├──────────────────────────────────────────────────────────────┤
│ Controls                                                    │
│ Sort | Source | Type | State | Watch Filter | Expand/Close  │
├──────────────────────────────────────────────────────────────┤
│ Group Section: Timer user                                   │
│  ├─ Card Grid                                               │
│  │  [Card] [Card] [Card] [Card] [Card]                      │
│  └─ ...                                                     │
├──────────────────────────────────────────────────────────────┤
│ Group Section: Service user                                 │
└──────────────────────────────────────────────────────────────┘
```

## 15.3 Mission Card

```text
┌───────────────────────────────────────────────┐
│ ● Name                           [☆] [state] │
│ script_name                                    │
├───────────────────────────────────────────────┤
│ Process only: uptime | cpu | ram | restart    │
├───────────────────────────────────────────────┤
│ Primary field             | Secondary field   │
│ Primary field             | Secondary field   │
│ Description full row                            │
├───────────────────────────────────────────────┤
│ [Loại] [Nguồn] [Nhóm] [Unit state] [PID] ...  │
├───────────────────────────────────────────────┤
│ [Theo dõi] [JSON]                             │
└───────────────────────────────────────────────┘
```

## 15.4 Settings / Config Page

```text
┌──────────────────────────────────────────────────────────────┐
│ Title + short explanation                                   │
├──────────────────────────────────────────────────────────────┤
│ Group Section: Main config                                  │
│  label      input                                            │
│  label      input                                            │
│  note                                                    btn │
├──────────────────────────────────────────────────────────────┤
│ Group Section: Danger zone                                  │
│  explanation                                         danger  │
└──────────────────────────────────────────────────────────────┘
```

## 15.5 Logs Page

```text
┌──────────────────────────────────────────────────────────────┐
│ Title + summary                                              │
├──────────────────────────────────────────────────────────────┤
│ Summary chips                                                │
├──────────────────────────────────────────────────────────────┤
│ Filters                                                      │
├──────────────────────────────────────────────────────────────┤
│ > process-name | source | health badge | last line | action │
│   expanded:                                                  │
│   source / recent activity / preformatted log                │
└──────────────────────────────────────────────────────────────┘
```

## 15.6 Knowledge Page

```text
┌──────────────────────────────────────────────────────────────┐
│ Summary stats                                                │
├──────────────────────────────────────────────────────────────┤
│ Scope chips                                                  │
├──────────────────────────────────────────────────────────────┤
│ Group: Lõi nhận thức                                         │
│  [Soul] [User] [Memory] [Learning] [Skill]                  │
├──────────────────────────────────────────────────────────────┤
│ Group: Bổ trợ                                                │
│  [Identity] [Agents] [Heartbeat]                            │
└──────────────────────────────────────────────────────────────┘
```

## 15.7 Backup Page

```text
┌──────────────────────────────────────────────────────────────┐
│ Summary                                                      │
├──────────────────────────────────────────────────────────────┤
│ Group: Critical                                              │
│  [Workspace] [Knowledge] [Missions]                         │
├──────────────────────────────────────────────────────────────┤
│ Group: Operational                                           │
│  [Skills] [Reminders] [Git Packages]                        │
├──────────────────────────────────────────────────────────────┤
│ Card actions: Download | Restore | JSON                     │
└──────────────────────────────────────────────────────────────┘
```

## 15.8 Responsive intent

Desktop lớn:
- ưu tiên nhiều cột
- dense card grid

Laptop:
- giảm 1-2 cột

Tablet:
- 2 cột

Mobile:
- 1 cột
- controls xuống nhiều hàng
