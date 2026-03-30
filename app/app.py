import base64
import datetime
import glob
import io
import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from urllib.parse import urlparse

import requests
from flask import Flask, Response, jsonify, redirect, render_template, request, send_file, session, url_for

app = Flask(__name__)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(APP_DIR)
SKIP_WALK_DIRS = {"dashboard", "backups", "__pycache__", ".git"}
OPENCLAW_ACCESS_CACHE_TTL = 45
OPENCLAW_ACCESS_CACHE = {"ts": 0.0, "value": None}


def load_env_file(path):
    """
    Lightweight .env reader used on production VPSes where we want the package
    to stay self-contained and avoid extra runtime dependencies such as
    python-dotenv.
    """
    if not path or not os.path.exists(path):
        return
    for raw_line in open(path, "r", encoding="utf-8", errors="replace"):
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value[:1] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


load_env_file(os.environ.get("AQUA_ENV_FILE") or os.path.join(PROJECT_DIR, ".env"))


def env(name, default):
    return os.environ.get(name, default)


def env_int(name, default):
    try:
        return int(os.environ.get(name, default))
    except Exception:
        return int(default)


def env_bool(name, default=False):
    raw = str(os.environ.get(name, "")).strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    return bool(default)


# These values are intentionally environment-driven so the same package can be
# reused on another VPS or another OpenClaw workspace without editing code.
OPENCLAW_HOME = env("AQUA_OPENCLAW_HOME", os.path.expanduser("~/.openclaw"))
WORKSPACE_DIR = env("AQUA_WORKSPACE_DIR", os.path.join(OPENCLAW_HOME, "workspace"))
TOOLS_DIR = env("AQUA_TOOLS_DIR", os.path.join(WORKSPACE_DIR, "tools"))
DATA_DIR = env("AQUA_DATA_DIR", os.path.join(WORKSPACE_DIR, "data"))
SKILLS_DIR = env("AQUA_SKILLS_DIR", os.path.join(WORKSPACE_DIR, "skills"))
BACKUP_DIR = env("AQUA_BACKUP_DIR", os.path.join(WORKSPACE_DIR, "backups"))
AUTH_PROFILES = env("AQUA_AUTH_PROFILES", os.path.join(OPENCLAW_HOME, "agents/main/agent/auth-profiles.json"))
GATEWAY_URL = env("AQUA_GATEWAY_URL", "http://127.0.0.1:18789")
OPENCLAW_BIN = env("AQUA_OPENCLAW_BIN", shutil.which("openclaw") or "/home/ubuntu/.npm-global/bin/openclaw")
PM2_BIN = env("AQUA_PM2_BIN", shutil.which("pm2") or "/home/ubuntu/.npm-global/bin/pm2")
APP_HOST = env("AQUA_HOST", "0.0.0.0")
APP_PORT = env_int("AQUA_PORT", 6080)

app.secret_key = env("AQUA_SECRET_KEY", "AQUA_DASHBOARD_SECRET")
ADMIN_PASSWORD = env("AQUA_ADMIN_PASSWORD", "AQUA_2026")

os.makedirs(BACKUP_DIR, exist_ok=True)

BACKUP_TARGETS = {
    "missions": {
        "label": "🚀 Nhiệm Vụ",
        "type": "dir_filter",
        "dir": WORKSPACE_DIR,
        "ext": [".sh", ".py"],
        "restore_dir": WORKSPACE_DIR,
        "importance": "high",
        "group": "Nhiệm Vụ",
    },
    "knowledge": {
        "label": "🧠 Tàng Thư Các",
        "files": [os.path.join(WORKSPACE_DIR, f) for f in ["SOUL.md", "USER.md", "MEMORY.md", "LEARNINGS.md", "TOOLS.md", "IDENTITY.md", "AGENTS.md", "HEARTBEAT.md"]],
        "type": "files",
        "restore_dir": WORKSPACE_DIR,
        "importance": "high",
        "group": "Tàng Thư Các",
    },
    "reminders": {
        "label": "⏰ Nhắc Việc",
        "files": [os.path.join(DATA_DIR, "assistant_hub.json")],
        "type": "files",
        "restore_dir": DATA_DIR,
        "importance": "high",
        "group": "Nhắc Việc",
    },
    "skills": {
        "label": "🧰 Skill Forge",
        "type": "dir_filter",
        "dir": TOOLS_DIR,
        "ext": [".sh", ".py"],
        "restore_dir": TOOLS_DIR,
        "importance": "high",
        "group": "Skill Forge",
    },
    "git-packages": {
        "label": "📦 Gói Github",
        "type": "dir",
        "dir": SKILLS_DIR,
        "restore_dir": SKILLS_DIR,
        "importance": "medium",
        "group": "Gói Github",
    },
    "full": {
        "label": "🌟 Toàn Bộ Workspace",
        "type": "workspace",
        "dir": WORKSPACE_DIR,
        "restore_dir": WORKSPACE_DIR,
        "importance": "critical",
        "group": "Workspace",
    },
}


def login_required(f):
    def wrap(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    wrap.__name__ = f.__name__
    return wrap


def run_cmd(cmd, timeout=5):
    """
    Small shell helper kept for backwards-compatible operational probes.
    Prefer env-driven absolute binaries (for example PM2_BIN / OPENCLAW_BIN)
    when calling external tools so a fresh VPS does not depend on PATH layout.
    """
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, timeout=timeout).decode().strip()
    except Exception:
        return ""


def safe_read(path, encoding="utf-8"):
    try:
        with open(path, "r", encoding=encoding, errors="replace") as handle:
            return handle.read()
    except Exception:
        return ""


def sanitize_leaf_name(name, allowed_exts=None):
    """
    Accept only plain filenames for upload/delete/read routes.
    This keeps dashboard file actions compatible with future OpenClaw layouts
    while blocking path traversal and accidental nested writes.
    """
    raw = str(name or "").strip()
    leaf = os.path.basename(raw)
    if not leaf or leaf in {".", ".."}:
        return None
    if raw != leaf or "/" in raw or "\\" in raw:
        return None
    if allowed_exts and not any(leaf.endswith(ext) for ext in allowed_exts):
        return None
    return leaf


def safe_restore_dest(base_dir, member_name):
    """
    Restore ZIP entries only inside the configured restore root.
    We normalize the archive path and then verify the final realpath stays
    under base_dir so a crafted ZIP cannot escape the target directory.
    """
    raw = str(member_name or "").replace("\\", "/").lstrip("/")
    normalized = os.path.normpath(raw)
    if not normalized or normalized in {".", ".."}:
        return None, None
    if normalized.startswith("../") or normalized.startswith("/"):
        return None, None
    base_real = os.path.realpath(base_dir)
    dest_real = os.path.realpath(os.path.join(base_real, normalized))
    try:
        if os.path.commonpath([base_real, dest_real]) != base_real:
            return None, None
    except ValueError:
        return None, None
    return dest_real, normalized


def tail_lines(path, count=40):
    content = safe_read(path)
    if not content:
        return []
    return content.splitlines()[-count:]


def format_ts(ts):
    if not ts:
        return ""
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def human_size(num):
    try:
        num = float(num)
    except Exception:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    for unit in units:
        if num < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(num)} {unit}"
            return f"{num:.1f} {unit}"
        num /= 1024
    return "0 B"


def normalize_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def decode_jwt(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        payload += "=" * (-len(payload) % 4)
        decoded = base64.b64decode(payload).decode("utf-8")
        return json.loads(decoded)
    except Exception:
        return {}


def git_remote(fp):
    cfg = os.path.join(fp, ".git", "config")
    if not os.path.exists(cfg):
        return None
    try:
        for line in safe_read(cfg).splitlines():
            if "url =" in line:
                return line.split("=", 1)[1].strip()
    except Exception:
        pass
    return None


def git_branch(fp):
    head = os.path.join(fp, ".git", "HEAD")
    if not os.path.exists(head):
        return None
    content = safe_read(head).strip()
    if content.startswith("ref:"):
        return content.rsplit("/", 1)[-1]
    return content[:12] if content else None


def git_host(remote):
    if not remote:
        return None
    if remote.startswith("git@") and ":" in remote:
        return remote.split("@", 1)[1].split(":", 1)[0]
    parsed = urlparse(remote)
    return parsed.netloc or None


def git_remote_path(remote):
    if not remote:
        return None
    if remote.startswith("git@") and ":" in remote:
        return remote.split(":", 1)[1].removesuffix(".git")
    parsed = urlparse(remote)
    return parsed.path.lstrip("/").removesuffix(".git") or None


def detect_importance(text, fallback="normal"):
    text = normalize_text(text)
    critical = ["gateway", "restore", "backup", "mission", "assistant", "scheduler", "dashboard", "bot", "trade", "system"]
    medium = ["browser", "ocr", "telegram", "workflow", "session", "auth", "monitor"]
    if any(token in text for token in critical):
        return "critical"
    if any(token in text for token in medium):
        return "high"
    return fallback


def detect_skill_group(name, content):
    name_l = normalize_text(name)
    content_l = normalize_text(content[:5000])
    if name_l.startswith("gui_ocr") or "ocr" in name_l:
        return "GUI / OCR"
    if name_l.startswith("gui_browser") or "chrome" in name_l or "brave" in name_l or "browser" in name_l:
        return "GUI / Browser"
    if name_l.startswith("gui_"):
        return "GUI / Control"
    if name_l.startswith("assistant_"):
        return "Assistant / Scheduler"
    if name_l.startswith("reminder_"):
        return "Assistant / Reminder"
    if name_l.startswith("sys_"):
        return "System / Package"
    if name_l.startswith("trade_") or name_l.startswith("crypto_") or "invest" in name_l:
        return "Trading / Finance"
    if "telegram" in name_l or "telegram" in content_l:
        return "Messaging / Telegram"
    if "dashboard" in name_l:
        return "Dashboard / Web"
    if "backup" in name_l or "restore" in name_l:
        return "Backup / Restore"
    if "session" in name_l or "state" in name_l:
        return "Session / State"
    return "General / Utility"


def detect_skill_tags(name, content):
    sample = normalize_text(f"{name} {content[:6000]}")
    tags = []
    rules = [
        ("telegram", "telegram"),
        ("browser", "browser"),
        ("chrome", "chrome"),
        ("brave", "brave"),
        ("ocr", "ocr"),
        ("pm2", "pm2"),
        ("curl", "http"),
        ("ssh", "ssh"),
        ("cron", "schedule"),
        ("scheduler", "schedule"),
        ("backup", "backup"),
        ("restore", "restore"),
        ("json", "json"),
        ("playwright", "playwright"),
    ]
    for needle, tag in rules:
        if needle in sample and tag not in tags:
            tags.append(tag)
    return tags[:6]


def detect_package_group(name, desc):
    sample = normalize_text(f"{name} {desc}")
    if "telegram" in sample:
        return "Messaging"
    if "trade" in sample or "invest" in sample or "market" in sample:
        return "Trading"
    if "browser" in sample or "chrome" in sample or "playwright" in sample:
        return "Browser"
    if "ocr" in sample:
        return "OCR"
    if "dashboard" in sample or "web" in sample:
        return "Dashboard"
    if "memory" in sample or "knowledge" in sample:
        return "Knowledge"
    return "Utility"


def detect_process_group(name, script):
    sample = normalize_text(f"{name} {script}")
    if "dashboard" in sample:
        return "Dashboard"
    if "gateway" in sample or name == "bot":
        return "Gateway"
    if "assistant" in sample or "scheduler" in sample:
        return "Scheduler"
    if "mission" in sample:
        return "Mission"
    return "Worker"


def file_metrics(path):
    content = safe_read(path)
    lines = content.splitlines()
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith("#") and not line.strip().startswith("#!"))
    import_lines = sum(
        1
        for line in lines
        if line.strip().startswith("import ")
        or line.strip().startswith("from ")
        or line.strip().startswith("source ")
        or re.match(r"^\.\s+\S+", line.strip())
    )
    code_lines = max(0, len(lines) - blank_lines - comment_lines)
    shebang = lines[0].strip() if lines and lines[0].startswith("#!") else ""
    return {
        "content": content,
        "lines": len(lines),
        "blank_lines": blank_lines,
        "comment_lines": comment_lines,
        "code_lines": code_lines,
        "import_lines": import_lines,
        "shebang": shebang,
    }


def dir_metrics(path, allowed_ext=None, skip_dirs=None):
    total_size = 0
    total_files = 0
    last_modified = 0
    ext_counter = {"py": 0, "sh": 0, "md": 0, "json": 0, "yml": 0, "other": 0}
    top_files = []
    skip_dirs = set(skip_dirs or [])
    if not os.path.exists(path):
        return {
            "file_count": 0,
            "total_size": 0,
            "size_human": "0 B",
            "last_modified": "",
            "py_count": 0,
            "sh_count": 0,
            "md_count": 0,
            "json_count": 0,
            "yml_count": 0,
            "other_count": 0,
            "top_files": [],
        }
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if allowed_ext and ext not in allowed_ext:
                continue
            fp = os.path.join(root, filename)
            try:
                stat = os.stat(fp)
            except OSError:
                continue
            size = stat.st_size
            total_size += size
            total_files += 1
            last_modified = max(last_modified, stat.st_mtime)
            rel = os.path.relpath(fp, path)
            top_files.append((size, rel))
            bucket = ext.lstrip(".")
            if bucket in ext_counter:
                ext_counter[bucket] += 1
            elif ext in {".yaml"}:
                ext_counter["yml"] += 1
            else:
                ext_counter["other"] += 1
    top_files.sort(reverse=True)
    return {
        "file_count": total_files,
        "total_size": total_size,
        "size_human": human_size(total_size),
        "last_modified": format_ts(last_modified),
        "py_count": ext_counter["py"],
        "sh_count": ext_counter["sh"],
        "md_count": ext_counter["md"],
        "json_count": ext_counter["json"],
        "yml_count": ext_counter["yml"],
        "other_count": ext_counter["other"],
        "top_files": [{"name": name, "size": human_size(size)} for size, name in top_files[:5]],
    }


def backup_target_summary(key, cfg):
    info = {
        "key": key,
        "label": cfg["label"],
        "type": cfg["type"],
        "importance": cfg.get("importance", "normal"),
        "group": cfg.get("group", "general"),
        "scope": cfg.get("restore_dir", ""),
    }
    file_count = 0
    total_size = 0
    last_modified = 0
    if cfg["type"] == "files":
        for fp in cfg["files"]:
            if not os.path.exists(fp):
                continue
            stat = os.stat(fp)
            file_count += 1
            total_size += stat.st_size
            last_modified = max(last_modified, stat.st_mtime)
    elif cfg["type"] == "dir_filter":
        metrics = dir_metrics(cfg["dir"], allowed_ext=set(cfg.get("ext", [])))
        file_count = metrics["file_count"]
        total_size = metrics["total_size"]
        last_modified = 0
    else:
        metrics = dir_metrics(cfg["dir"], skip_dirs=SKIP_WALK_DIRS)
        file_count = metrics["file_count"]
        total_size = metrics["total_size"]
        last_modified = 0
    info.update(
        {
            "file_count": file_count,
            "size_bytes": total_size,
            "size_human": human_size(total_size),
            "last_updated": format_ts(last_modified),
        }
    )
    return info


def mask_secret(secret, head=6, tail=4):
    secret = str(secret or "")
    if not secret:
        return ""
    if len(secret) <= head + tail:
        return secret
    return f"{secret[:head]}...{secret[-tail:]}"


def telegram_chat_kind(chat_id):
    chat_id = str(chat_id or "").strip()
    if not chat_id:
        return "unknown"
    if chat_id == "*":
        return "default"
    try:
        return "group" if int(chat_id) < 0 else "user"
    except Exception:
        return "unknown"


def extract_numeric_ids(text):
    return re.findall(r"(?<!\d)-?\d{6,16}(?!\d)", str(text or ""))


def add_telegram_candidate(store, chat_id, source, role="", current=False, excerpt="", kind=None):
    key = str(chat_id or "").strip()
    if not key:
        return
    item = store.setdefault(
        key,
        {
            "id": key,
            "kind": kind or telegram_chat_kind(key),
            "role": role or "Ứng viên Telegram",
            "current": False,
            "sources": [],
            "excerpts": [],
        },
    )
    if kind and item.get("kind") in {"unknown", None, ""}:
        item["kind"] = kind
    if role and item.get("role") in {"", "Ứng viên Telegram"}:
        item["role"] = role
    item["current"] = bool(item.get("current") or current)
    if source and source not in item["sources"]:
        item["sources"].append(source)
    if excerpt:
        excerpt = re.sub(r"\s+", " ", excerpt).strip()
        if excerpt and excerpt not in item["excerpts"]:
            item["excerpts"].append(excerpt[:220])


def load_telegram_access_data():
    raw_cfg = safe_read(os.path.join(OPENCLAW_HOME, "openclaw.json")) or "{}"
    try:
        cfg = json.loads(raw_cfg)
    except Exception:
        cfg = {}

    telegram_cfg = cfg.get("channels", {}).get("telegram", {}) or {}
    session_cfg = cfg.get("session", {}) or {}
    approvals_cfg = cfg.get("approvals", {}).get("exec", {}) or {}
    exec_targets = [t for t in approvals_cfg.get("targets", []) if t.get("channel") == "telegram"]
    exec_target_ids = {str(t.get("to")) for t in exec_targets if t.get("to") is not None}

    bot_token = telegram_cfg.get("botToken", "")
    bot_id = bot_token.split(":", 1)[0] if ":" in bot_token else ""

    groups = []
    candidates = {}
    for group_id, policy in (telegram_cfg.get("groups", {}) or {}).items():
        allow_from = [str(x) for x in (policy.get("allowFrom", []) or [])]
        explicit_ids = [x for x in allow_from if x != "*"]
        allow_any = "*" in allow_from
        kind = telegram_chat_kind(group_id)
        if kind in {"group", "user"}:
            add_telegram_candidate(
                candidates,
                group_id,
                "Cấu hình live / groups",
                role="Chat đang có trong config live",
                current=True,
                excerpt=f"group {group_id}",
                kind=kind,
            )
        for actor_id in explicit_ids:
            add_telegram_candidate(
                candidates,
                actor_id,
                f"Cấu hình live / allowFrom của {group_id}",
                role="ID được phép trong nhóm",
                current=True,
                excerpt=f"allowFrom {group_id}: {actor_id}",
                kind=telegram_chat_kind(actor_id),
            )
        groups.append(
            {
                "id": str(group_id),
                "kind": kind,
                "kind_label": "Mặc định" if kind == "default" else "Nhóm" if kind == "group" else "User" if kind == "user" else "Khác",
                "require_mention": bool(policy.get("requireMention", False)),
                "allow_from": allow_from,
                "allow_from_any": allow_any,
                "allow_from_count": len(explicit_ids),
                "is_exec_target": str(group_id) in exec_target_ids,
                "source": "live",
            }
        )

    for target in exec_targets:
        target_id = str(target.get("to") or "").strip()
        if target_id:
            add_telegram_candidate(
                candidates,
                target_id,
                "approvals.exec.targets",
                role="Đích nhận exec approval",
                current=True,
                excerpt=f"approval target {target_id}",
                kind=telegram_chat_kind(target_id),
            )

    bot_identity = os.path.join(WORKSPACE_DIR, "bot_identity.md")
    if os.path.exists(bot_identity):
        for line in safe_read(bot_identity).splitlines():
            if "telegram user id" not in line.lower():
                continue
            for match in extract_numeric_ids(line):
                add_telegram_candidate(
                    candidates,
                    match,
                    "workspace/bot_identity.md",
                    role="Admin / chủ bot được ghi nhận",
                    current=False,
                    excerpt=line,
                    kind="user",
                )

    memory_dir = os.path.join(WORKSPACE_DIR, "memory")
    if os.path.isdir(memory_dir):
        memory_files = sorted(
            [os.path.join(memory_dir, name) for name in os.listdir(memory_dir) if name.endswith(".md")]
        )[-20:]
        for path in memory_files:
            basename = os.path.basename(path)
            for no, line in enumerate(safe_read(path).splitlines(), start=1):
                lower = line.lower()
                if "telegram" not in lower and "allowlist" not in lower and "admin" not in lower and "group id" not in lower:
                    continue
                role = "Nhật ký Telegram"
                if "admin" in lower or "allowlist" in lower:
                    role = "Admin được nhắc tới"
                elif "group" in lower:
                    role = "Nhóm Telegram được nhắc tới"
                for match in extract_numeric_ids(line):
                    add_telegram_candidate(
                        candidates,
                        match,
                        f"memory/{basename}:{no}",
                        role=role,
                        current=False,
                        excerpt=line,
                        kind=telegram_chat_kind(match),
                    )

    snapshots = []
    for path in sorted(glob.glob(os.path.join(OPENCLAW_HOME, "openclaw.json.clobbered.*")))[-30:]:
        try:
            obj = json.loads(safe_read(path) or "{}")
        except Exception:
            continue
        snap_tg = obj.get("channels", {}).get("telegram") or obj.get("telegram") or {}
        if not snap_tg:
            continue
        allowed_chats = [str(x) for x in (snap_tg.get("allowedChats") or [])]
        group_keys = [str(x) for x in (snap_tg.get("groups") or {}).keys()]
        schema = "groups" if snap_tg.get("groups") is not None else "allowedChats" if snap_tg.get("allowedChats") is not None else "telegram"
        try:
            stat = os.stat(path)
            updated_at = format_ts(stat.st_mtime)
        except OSError:
            updated_at = ""
        snapshots.append(
            {
                "file": os.path.basename(path),
                "updated_at": updated_at,
                "schema": schema,
                "allowed_chats": allowed_chats,
                "group_keys": group_keys,
            }
        )
        for match in allowed_chats + group_keys:
            add_telegram_candidate(
                candidates,
                match,
                os.path.basename(path),
                role="ID từng có trong snapshot cấu hình",
                current=False,
                excerpt=f"schema={schema}",
                kind=telegram_chat_kind(match),
            )

    actors = []
    for item in candidates.values():
        kind = item.get("kind") or telegram_chat_kind(item["id"])
        item["kind"] = kind
        if kind == "group":
            item["kind_label"] = "Nhóm Telegram"
        elif kind == "user":
            item["kind_label"] = "User / Admin Telegram"
        elif kind == "default":
            item["kind_label"] = "Mặc định"
        else:
            item["kind_label"] = "Khác"
        item["source_label"] = " | ".join(item.get("sources", []))
        item["excerpt"] = item.get("excerpts", [""])[0] if item.get("excerpts") else ""
        actors.append(item)

    actors.sort(key=lambda entry: (not entry.get("current", False), entry.get("kind") != "group", entry.get("id")))

    return {
        "config": {
            "enabled": bool(telegram_cfg.get("enabled")),
            "bot_id": bot_id,
            "bot_token_masked": mask_secret(bot_token),
            "group_policy": telegram_cfg.get("groupPolicy", ""),
            "dm_policy": telegram_cfg.get("dmPolicy", ""),
            "dm_scope": session_cfg.get("dmScope", ""),
            "streaming": telegram_cfg.get("streaming", ""),
            "exec_approvals_enabled": bool((telegram_cfg.get("execApprovals") or {}).get("enabled")),
            "exec_approvals_target": (telegram_cfg.get("execApprovals") or {}).get("target", ""),
            "approval_mode": approvals_cfg.get("mode", ""),
            "approval_agent_filter": approvals_cfg.get("agentFilter", []) or [],
            "exec_targets": [str(t.get("to")) for t in exec_targets if t.get("to") is not None],
        },
        "groups": sorted(groups, key=lambda item: (item.get("kind") != "default", item.get("id", ""))),
        "actors": actors,
        "snapshots": sorted(snapshots, key=lambda item: item.get("file", ""), reverse=True)[:12],
    }


def get_openclaw_access_info():
    """
    OpenClaw itself stays untouched. We only ask its CLI for the current
    tokenized dashboard URL and cache the result briefly because the command is
    slow and would otherwise make the dashboard feel laggy on every tab visit.
    """
    now = time.time()
    cached = OPENCLAW_ACCESS_CACHE.get("value")
    if cached and now - float(OPENCLAW_ACCESS_CACHE.get("ts") or 0.0) < OPENCLAW_ACCESS_CACHE_TTL:
        return cached
    output = ""
    url = ""
    base_url = ""
    token = ""
    try:
        proc = subprocess.run(
            [OPENCLAW_BIN, "dashboard", "--no-open"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    except Exception as exc:
        output = str(exc)
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("Dashboard URL:"):
            url = line.split("Dashboard URL:", 1)[1].strip()
            break
    if url:
        base_url = url.split("#", 1)[0]
        if "#token=" in url:
            token = url.split("#token=", 1)[1].strip()
    result = {
        "ok": bool(url),
        "dashboard_url": url,
        "base_url": base_url,
        "token": token,
        "tunnel_command": "ssh -N -L 18789:127.0.0.1:18789 -p 10900 ubuntu@e1.chiasegpu.vn",
        "local_open": "http://127.0.0.1:18789/",
        "public_proxy_url": "http://e1.chiasegpu.vn:35045/openclaw/",
        "public_dashboard_url": "http://e1.chiasegpu.vn:35045/",
        "reason_public": "Đường public /openclaw/ chỉ đi qua Flask proxy HTTP và không phải đường truy cập chuẩn cho WebSocket + token của OpenClaw.",
        "reason_root": "Mở root 127.0.0.1:18789 chỉ hiện màn Connect; muốn vào thẳng phải dùng URL có #token do openclaw dashboard sinh ra.",
        "raw_output": output[-4000:],
    }
    OPENCLAW_ACCESS_CACHE["ts"] = now
    OPENCLAW_ACCESS_CACHE["value"] = result
    return result


@app.route("/api/telegram-access")
@login_required
def telegram_access():
    return jsonify(load_telegram_access_data())


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Sai mật khẩu!"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    html_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(content, mimetype="text/html")


@app.route("/openclaw")
@login_required
def openclaw_proxy_root():
    return redirect("/openclaw/")


@app.route("/openclaw/", defaults={"path": ""})
@app.route("/openclaw/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@login_required
def openclaw_proxy(path):
    # Compatibility proxy kept for light inspection only. The recommended
    # operator path is still "SSH tunnel + tokenized URL" because OpenClaw may
    # change its control UI/WebSocket behavior across upgrades.
    url = f"{GATEWAY_URL}/{path}"
    headers = {k: v for k, v in request.headers if k.lower() != "host"}
    try:
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10,
        )
        excluded_headers = {
            "content-encoding",
            "content-length",
            "transfer-encoding",
            "connection",
            "x-frame-options",
            "content-security-policy",
            "frame-options",
        }
        proxy_headers = [(name, value) for name, value in resp.raw.headers.items() if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, proxy_headers)
    except Exception as e:
        return f"OpenClaw Proxy Error: {str(e)}", 502


@app.route("/api/system")
@login_required
def system_stats():
    cpu = run_cmd("top -bn1 | grep 'Cpu(s)' | awk '{print $2+$4}'")
    try:
        cpu_pct = round(float(cpu), 1)
    except Exception:
        cpu_pct = 0.0
    mem = run_cmd("free -m | awk '/^Mem/{print $2,$3,$4,$7}'")
    try:
        total_mb, used_mb, free_mb, avail_mb = map(int, mem.split())
        ram_pct = round(used_mb / total_mb * 100, 1)
    except Exception:
        total_mb = used_mb = free_mb = avail_mb = 0
        ram_pct = 0.0
    disk = run_cmd("df -B1 / | awk 'NR==2{print $2,$3,$4,$5}'")
    try:
        d_total_b, d_used_b, d_free_b, d_pct_s = disk.split()
        d_total_b = int(d_total_b)
        d_used_b = int(d_used_b)
        d_free_b = int(d_free_b)
        d_total = human_size(d_total_b)
        d_used = human_size(d_used_b)
        d_free = human_size(d_free_b)
        d_pct = int(d_pct_s.rstrip("%"))
    except Exception:
        d_total_b = d_used_b = d_free_b = 0
        d_used = d_total = d_free = "?"
        d_pct = 0
    uptime = run_cmd("uptime -p").replace("up ", "")
    load = run_cmd("cat /proc/loadavg | awk '{print $1,$2,$3}'")
    hostname = run_cmd("hostname") or "unknown"
    return jsonify(
        {
            "cpu_pct": cpu_pct,
            "ram_pct": ram_pct,
            "ram_used_mb": used_mb,
            "ram_total_mb": total_mb,
            "ram_free_mb": free_mb,
            "ram_available_mb": avail_mb,
            "disk_pct": d_pct,
            "disk_used": d_used,
            "disk_total": d_total,
            "disk_free": d_free,
            "disk_used_bytes": d_used_b,
            "disk_total_bytes": d_total_b,
            "disk_free_bytes": d_free_b,
            "uptime": uptime,
            "load": load,
            "hostname": hostname,
        }
    )


@app.route("/api/tokens")
@login_required
def get_tokens():
    tokens = []
    now = datetime.datetime.now().timestamp()
    try:
        cfg = json.loads(safe_read(os.path.join(OPENCLAW_HOME, "openclaw.json")) or "{}")
        gk = cfg.get("entries", {}).get("google", {}).get("config", {}).get("webSearch", {}).get("apiKey", "")
        if gk:
            tokens.append(
                {
                    "name": "Google Search API",
                    "provider": "Google",
                    "type": "api_key",
                    "status": "ACTIVE",
                    "priority": "medium",
                    "info": f"{gk[:6]}...{gk[-4:]}",
                    "days_left": None,
                    "total_days": None,
                    "pct_left": None,
                    "issued_at": None,
                    "expiry": None,
                }
            )
    except Exception:
        pass

    if os.path.exists(AUTH_PROFILES):
        try:
            data = json.loads(safe_read(AUTH_PROFILES) or "{}")
            for key, prof in data.get("profiles", {}).items():
                if prof.get("provider") != "openai-codex":
                    continue
                token = prof.get("access", "")
                payload = decode_jwt(token)
                iat = payload.get("iat")
                exp = payload.get("exp")
                total_days = round((exp - iat) / 86400, 1) if exp and iat and exp > iat else None
                exp_date = datetime.datetime.fromtimestamp(exp).strftime("%Y-%m-%d %H:%M:%S") if exp else "Unknown"
                issued_date = datetime.datetime.fromtimestamp(iat).strftime("%Y-%m-%d %H:%M:%S") if iat else None
                days_left = round((exp - now) / 86400, 1) if exp else -1
                pct_left = round(max(0, min(100, (days_left / total_days) * 100)), 1) if total_days and total_days > 0 else None
                status = "EXPIRED" if days_left < 0 else "WARNING" if days_left < 2 else "ACTIVE"
                priority = "critical" if days_left < 1 else "high" if days_left < 3 else "medium"
                tokens.append(
                    {
                        "name": "ChatGPT OAuth (OpenAI)",
                        "provider": "OpenAI",
                        "type": "oauth",
                        "status": status,
                        "priority": priority,
                        "info": key.split(":")[-1] if ":" in key else key,
                        "expiry": exp_date,
                        "issued_at": issued_date,
                        "days_left": days_left,
                        "total_days": total_days,
                        "pct_left": pct_left,
                    }
                )
        except Exception:
            pass
    return jsonify(tokens)


@app.route("/api/logs/openclaw")
@login_required
def get_openclaw_logs():
    names = ["bot", "GodMode_Mission", "assistant_scheduler", "aqua_dashboard"]
    raw = run_cmd(f'"{PM2_BIN}" jlist', timeout=8)
    proc_map = {}
    try:
        for proc in json.loads(raw or "[]"):
            proc_map[proc.get("name")] = proc.get("pm2_env", {})
    except Exception:
        proc_map = {}
    items = []
    for name in names:
        env = proc_map.get(name, {})
        out_lines = tail_lines(env.get("pm_out_log_path", ""), 12)
        err_lines = tail_lines(env.get("pm_err_log_path", ""), 12)
        last_line = (err_lines[-1] if err_lines else out_lines[-1] if out_lines else "").strip()
        items.append(
            {
                "name": name,
                "out_lines": out_lines,
                "error_lines": err_lines,
                "last_line": last_line,
                "error_count": len(err_lines),
                "has_activity": bool(out_lines or err_lines),
            }
        )
    return jsonify(items)


@app.route("/api/openclaw-access")
@login_required
def openclaw_access():
    if str(request.args.get("refresh", "")).lower() in {"1", "true", "yes"}:
        OPENCLAW_ACCESS_CACHE["ts"] = 0.0
        OPENCLAW_ACCESS_CACHE["value"] = None
    return jsonify(get_openclaw_access_info())


@app.route("/api/missions")
@login_required
def get_missions():
    raw = run_cmd(f'"{PM2_BIN}" jlist', timeout=8)
    if not raw:
        return jsonify([])
    try:
        procs = json.loads(raw)
    except Exception:
        return jsonify([])

    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    missions = []
    for proc in procs:
        pm_env = proc.get("pm2_env", {})
        script = pm_env.get("pm_exec_path", "")
        uptime_ms = pm_env.get("pm_uptime", 0)
        uptime_s = max(0, (now_ms - uptime_ms) // 1000) if uptime_ms else 0
        if uptime_s < 60:
            uptime = f"{uptime_s}s"
        elif uptime_s < 3600:
            uptime = f"{uptime_s // 60}m {uptime_s % 60}s"
        else:
            uptime = f"{uptime_s // 3600}h {(uptime_s % 3600) // 60}m"

        script_size = 0
        updated_at = ""
        steps = []
        desc = ""
        line_count = 0
        if script and os.path.exists(script):
            content = safe_read(script)
            lines = content.splitlines()
            line_count = len(lines)
            try:
                stat = os.stat(script)
                script_size = stat.st_size
                updated_at = format_ts(stat.st_mtime)
            except OSError:
                pass
            for line in lines[:6]:
                line = line.strip()
                if line.startswith("#") and not line.startswith("#!") and line.strip("#").strip():
                    desc = desc or line.strip("#").strip()
            for line in lines:
                line = line.strip()
                if line.startswith("# Step") or line.startswith("# STEP") or line.startswith("# Bước"):
                    steps.append(line.lstrip("#").strip())
                elif re.match(r"^# \d+\.", line):
                    steps.append(line.lstrip("#").strip())

        group = detect_process_group(proc.get("name", ""), script)
        importance = detect_importance(f"{proc.get('name','')} {script}", fallback="medium")
        missions.append(
            {
                "id": proc.get("pm_id"),
                "name": proc.get("name", ""),
                "group": group,
                "importance": importance,
                "status": pm_env.get("status", "unknown"),
                "pid": proc.get("pid", 0),
                "uptime": uptime,
                "restarts": pm_env.get("restart_time", 0),
                "cpu": proc.get("monit", {}).get("cpu", 0),
                "mem_mb": round(proc.get("monit", {}).get("memory", 0) / (1024 * 1024), 1),
                "script": script,
                "script_name": os.path.basename(script) if script else "",
                "script_size": human_size(script_size),
                "script_size_bytes": script_size,
                "script_updated_at": updated_at,
                "cwd": pm_env.get("pm_cwd", ""),
                "interpreter": proc.get("pm2_env", {}).get("exec_interpreter", ""),
                "exec_mode": pm_env.get("exec_mode", ""),
                "desc": desc or proc.get("name", ""),
                "steps": steps[:12],
                "step_count": len(steps),
                "line_count": line_count,
            }
        )
    return jsonify(sorted(missions, key=lambda item: (item.get("group", ""), item.get("id", 0))))


@app.route("/api/reminders")
@login_required
def get_reminders():
    try:
        with open(os.path.join(DATA_DIR, "assistant_hub.json"), "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify({"reminders": [], "proposals": [], "alerts": [], "daily_reports": [], "meta": {}})


@app.route("/api/skills", methods=["GET"])
@login_required
def get_skills():
    skills = []
    for filename in sorted(os.listdir(TOOLS_DIR)):
        if not (filename.endswith(".sh") or filename.endswith(".py")):
            continue
        path = os.path.join(TOOLS_DIR, filename)
        try:
            stat = os.stat(path)
        except OSError:
            continue
        metrics = file_metrics(path)
        content = metrics.pop("content")
        group = detect_skill_group(filename, content)
        importance = detect_importance(f"{filename} {group} {content[:1000]}", fallback="medium")
        ext = os.path.splitext(filename)[1].lstrip(".")
        lang = "python" if ext == "py" else "shell" if ext == "sh" else ext
        tags = detect_skill_tags(filename, content)
        desc = "Không có mô tả"
        for line in content.splitlines()[:8]:
            line = line.strip()
            if line.startswith("#") and not line.startswith("#!"):
                desc = line.lstrip("# ").strip()
                break
        skills.append(
            {
                "name": filename,
                "path": path,
                "ext": ext,
                "lang": lang,
                "group": group,
                "importance": importance,
                "size": stat.st_size,
                "size_human": human_size(stat.st_size),
                "updated_at": format_ts(stat.st_mtime),
                "installed": os.access(path, os.X_OK),
                "desc": desc,
                "tags": tags,
                **metrics,
            }
        )
    return jsonify(skills)


@app.route("/api/skills/<filename>/content")
@login_required
def skill_content(filename):
    filename = sanitize_leaf_name(filename, allowed_exts={".py", ".sh"})
    if not filename:
        return jsonify({"error": "Invalid"}), 400
    path = os.path.join(TOOLS_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    try:
        content = safe_read(path)
        return jsonify({"content": content, "ext": filename.rsplit(".", 1)[-1] if "." in filename else ""})
    except Exception:
        return jsonify({"error": "Error reading file"}), 500


@app.route("/api/skills", methods=["POST"])
@login_required
def upload_skill():
    f = request.files.get("file")
    filename = sanitize_leaf_name(getattr(f, "filename", ""), allowed_exts={".py", ".sh"}) if f else None
    if f and filename:
        fp = os.path.join(TOOLS_DIR, filename)
        f.save(fp)
        if filename.endswith(".sh"):
            os.chmod(fp, 0o775)
        return jsonify({"status": "ok"})
    return jsonify({"error": "Invalid file"}), 400


@app.route("/api/skills/<filename>", methods=["DELETE"])
@login_required
def delete_skill(filename):
    filename = sanitize_leaf_name(filename, allowed_exts={".py", ".sh"})
    if filename:
        try:
            os.remove(os.path.join(TOOLS_DIR, filename))
            return jsonify({"status": "ok"})
        except Exception:
            pass
    return jsonify({"error": "Error deleting"}), 400


@app.route("/api/git-packages")
@login_required
def get_git_packages():
    packages = []
    if not os.path.exists(SKILLS_DIR):
        return jsonify(packages)
    for foldername in sorted(os.listdir(SKILLS_DIR)):
        fp = os.path.join(SKILLS_DIR, foldername)
        if not os.path.isdir(fp) or foldername.startswith("."):
            continue
        meta_path = os.path.join(fp, "_meta.json")
        desc = "Gói Skill Github"
        if os.path.exists(meta_path):
            try:
                data = json.loads(safe_read(meta_path) or "{}")
                desc = data.get("description", desc)
            except Exception:
                pass
        metrics = dir_metrics(fp, skip_dirs=SKIP_WALK_DIRS)
        remote = git_remote(fp)
        branch = git_branch(fp)
        group = detect_package_group(foldername, desc)
        importance = detect_importance(f"{foldername} {desc}", fallback="medium")
        readme = any(os.path.exists(os.path.join(fp, name)) for name in ["README.md", "readme.md", "README.MD"])
        packages.append(
            {
                "name": foldername,
                "group": group,
                "importance": importance,
                "created_at": format_ts(os.stat(fp).st_mtime),
                "updated_at": metrics["last_modified"],
                "status": "OK",
                "desc": desc,
                "remote": remote,
                "remote_host": git_host(remote),
                "remote_path": git_remote_path(remote),
                "branch": branch,
                "has_meta": os.path.exists(meta_path),
                "has_readme": readme,
                **metrics,
            }
        )
    return jsonify(packages)


@app.route("/api/git-packages/<foldername>", methods=["DELETE"])
@login_required
def delete_git_package(foldername):
    foldername = sanitize_leaf_name(foldername)
    if foldername:
        fp = os.path.join(SKILLS_DIR, foldername)
        if os.path.exists(fp):
            try:
                shutil.rmtree(fp)
                return jsonify({"status": "ok"})
            except Exception:
                pass
    return jsonify({"error": "Error"}), 400


@app.route("/api/knowledge/<topic>")
@login_required
def get_knowledge(topic):
    valid = {
        "soul": "SOUL.md",
        "user": "USER.md",
        "memory": "MEMORY.md",
        "learning": "LEARNINGS.md",
        "skill": "TOOLS.md",
        "identity": "IDENTITY.md",
        "agents": "AGENTS.md",
        "heartbeat": "HEARTBEAT.md",
    }
    if topic.lower() in valid:
        fp = os.path.join(WORKSPACE_DIR, valid[topic.lower()])
        try:
            content = safe_read(fp)
            stat = os.stat(fp)
            return jsonify(
                {
                    "content": content,
                    "size_human": human_size(stat.st_size),
                    "updated_at": format_ts(stat.st_mtime),
                    "line_count": len(content.splitlines()),
                }
            )
        except Exception:
            pass
    return jsonify({"error": "Not found"}), 404


@app.route("/api/backup-targets")
@login_required
def backup_targets():
    return jsonify([backup_target_summary(key, cfg) for key, cfg in BACKUP_TARGETS.items()])


@app.route("/api/backup/<target>")
@login_required
def backup(target):
    if target not in BACKUP_TARGETS:
        return jsonify({"error": "Invalid"}), 400
    cfg = BACKUP_TARGETS[target]
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if cfg["type"] == "files":
            for fp in cfg["files"]:
                if os.path.exists(fp):
                    zf.write(fp, os.path.basename(fp))
        elif cfg["type"] == "dir_filter":
            for filename in os.listdir(cfg["dir"]):
                if any(filename.endswith(ext) for ext in cfg["ext"]):
                    zf.write(os.path.join(cfg["dir"], filename), filename)
        elif cfg["type"] in ("dir", "workspace"):
            base = cfg["dir"]
            for root, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in SKIP_WALK_DIRS]
                for filename in files:
                    full_path = os.path.join(root, filename)
                    zf.write(full_path, os.path.relpath(full_path, base))
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"aqua_backup_{target}_{ts}.zip")


@app.route("/api/restore/<target>", methods=["POST"])
@login_required
def restore(target):
    if target not in BACKUP_TARGETS:
        return jsonify({"error": "Invalid"}), 400
    zfile = request.files.get("file")
    if not zfile or not zfile.filename.endswith(".zip"):
        return jsonify({"error": "Invalid ZIP"}), 400
    try:
        buf = io.BytesIO(zfile.read())
        count = 0
        with zipfile.ZipFile(buf, "r") as zf:
            for member in zf.namelist():
                if member.endswith("/"):
                    continue
                dest, safe = safe_restore_dest(BACKUP_TARGETS[target]["restore_dir"], member)
                if not dest or not safe:
                    continue
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, "wb") as handle:
                    handle.write(zf.read(member))
                if dest.endswith(".sh"):
                    os.chmod(dest, 0o775)
                count += 1
        return jsonify({"status": "ok", "restored": count, "message": f"Đã phục hồi {count} file!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Host/port are env-driven so the same build can be installed on a
    # different VPS without touching source code.
    app.run(host=APP_HOST, port=APP_PORT)
