# 17. Tailwind Implementation Guide

Tài liệu này hướng dẫn cách hiện thực chuẩn UI AQUA bằng Tailwind hoặc CSS utility style.

## 17.1 Nguyên tắc
AQUA hiện là hybrid:
- có Tailwind nền
- có CSS custom mạnh

Vì vậy khi dựng UI mới:
- dùng Tailwind cho layout nhanh
- dùng token AQUA cho phần nhận diện
- không phụ thuộc hoàn toàn vào Tailwind defaults

## 17.2 Font

Tailwind nên map:
- `font-sans` -> Inter
- `font-mono` -> JetBrains Mono

Ví dụ:

```html
<div class="font-sans text-slate-200">...</div>
<code class="font-mono text-[11px]">...</code>
```

## 17.3 Container

```html
<main class="mx-auto w-[min(1780px,calc(100vw-40px))] px-5 py-5">
```

## 17.4 Topbar

```html
<header class="flex flex-wrap items-center justify-between gap-4">
```

## 17.5 Toolbar

```html
<section class="flex flex-wrap items-center justify-between gap-3 rounded-[18px] border border-slate-600 bg-slate-800 px-4 py-3">
```

## 17.6 Tabs

```html
<nav class="flex flex-wrap gap-3 rounded-[18px] border border-slate-600 bg-slate-800 p-3">
  <button class="min-h-12 min-w-[138px] rounded-[14px] border border-slate-500 bg-slate-700 px-4 py-3 text-[13px] font-extrabold text-slate-200">
    🚀 Nhiệm Vụ
  </button>
</nav>
```

### Active tab
- thêm nền semantic
- thêm text sáng hơn
- thêm inner highlight hoặc accent line nhẹ

## 17.7 Dense stat

```html
<div class="rounded-[20px] border border-slate-600 bg-slate-800 p-4">
  <div class="text-[10px] uppercase tracking-[0.06em] text-slate-400">CPU</div>
  <div class="mt-1 text-[14px] font-bold text-slate-50">84%</div>
  <div class="mt-1 text-[10px] text-slate-500">Load 0.2</div>
</div>
```

## 17.8 Dense card

```html
<article class="rounded-[20px] border border-slate-600 bg-slate-800 p-4 shadow-[0_8px_22px_rgba(4,10,20,.12)]">
```

### Nội bộ card
- top row: `flex items-start justify-between gap-2`
- detail grid: `grid grid-cols-3 gap-2`
- tag row: `flex flex-wrap gap-1`

## 17.9 Buttons

### Button thường

```html
<button class="inline-flex min-h-10 items-center gap-2 rounded-[14px] border border-slate-500 bg-slate-700 px-4 text-sm font-semibold text-slate-100">
```

### Button chính

```html
<button class="inline-flex min-h-10 items-center gap-2 rounded-[14px] border border-transparent bg-gradient-to-br from-violet-500 to-indigo-400 px-4 text-sm font-semibold text-white">
```

### Button danger

```html
<button class="inline-flex min-h-10 items-center gap-2 rounded-[14px] border border-rose-400/20 bg-rose-400/10 px-4 text-sm font-semibold text-rose-300">
```

## 17.10 Badge

### Neutral

```html
<span class="inline-flex items-center rounded-full border border-slate-600 bg-slate-700 px-2.5 py-1 text-[10px] font-bold text-slate-200">
```

### Success

```html
<span class="inline-flex items-center rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[10px] font-bold text-emerald-300">
```

### Warning

```html
<span class="inline-flex items-center rounded-full border border-amber-400/20 bg-amber-400/10 px-2.5 py-1 text-[10px] font-bold text-amber-300">
```

### Error

```html
<span class="inline-flex items-center rounded-full border border-rose-400/20 bg-rose-400/10 px-2.5 py-1 text-[10px] font-bold text-rose-300">
```

## 17.11 Inputs

```html
<input class="min-h-11 rounded-[14px] border border-slate-600 bg-slate-800 px-4 text-sm text-slate-100 placeholder:text-slate-500 focus:border-orange-300 focus:outline-none focus:ring-2 focus:ring-orange-300/20">
```

## 17.12 Tables

```html
<div class="overflow-auto rounded-[20px] border border-slate-600 bg-slate-800">
  <table class="min-w-full border-collapse">
```

### Header
- sticky nếu cần
- uppercase nhỏ
- muted

## 17.13 Log row

```html
<details class="overflow-hidden rounded-[20px] border border-slate-600 bg-slate-800">
  <summary class="grid grid-cols-[220px_140px_180px_1fr_auto] items-center gap-2 bg-slate-700 px-4 py-3 text-sm font-bold text-slate-50">
```

## 17.14 Responsive

### Tailwind gợi ý
- `xl:grid-cols-5`
- `lg:grid-cols-4`
- `md:grid-cols-3`
- `sm:grid-cols-2`
- `grid-cols-1`

### Với inventory dày
- desktop lớn: `5`
- laptop: `4`
- tablet: `2-3`
- mobile: `1`

## 17.15 Khi kết hợp Tailwind với CSS custom
- Tailwind lo layout và spacing tổng quát
- CSS custom lo:
  - token màu
  - gradient
  - tone semantic
  - state phức tạp

Không nên cố ép toàn bộ AQUA thành Tailwind thuần nếu làm mất sự ổn định của style system.
