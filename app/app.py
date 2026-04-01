import base64
import datetime
import glob
import io
import json
import os
import re
import shlex
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
TOKEN_RUNTIME_CACHE_TTL = 45
TOKEN_RUNTIME_CACHE = {"ts": 0.0, "value": None}


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
OPENCLAW_BIN = env("AQUA_OPENCLAW_BIN", shutil.which("openclaw") or "openclaw")
PM2_BIN = env("AQUA_PM2_BIN", shutil.which("pm2") or "pm2")
PM2_HOME = env("AQUA_PM2_HOME", os.path.join(os.path.expanduser("~"), ".pm2"))
APP_HOST = env("AQUA_HOST", "0.0.0.0")
APP_PORT = env_int("AQUA_PORT", 6080)
PUBLIC_BASE_URL = str(env("AQUA_PUBLIC_BASE_URL", "")).strip().rstrip("/")
SSH_HOST = str(env("AQUA_SSH_HOST", "")).strip()
SSH_PORT = str(env("AQUA_SSH_PORT", "22")).strip() or "22"
SSH_USER = str(env("AQUA_SSH_USER", "")).strip()
TUNNEL_LOCAL_PORT = env_int("AQUA_GATEWAY_TUNNEL_LOCAL_PORT", 18789)
SYSTEM_SERVICE_ALLOWLIST = [
    name.strip()
    for name in str(
        env(
            "AQUA_SYSTEM_SERVICE_ALLOWLIST",
            "ssh.service,xrdp.service,xrdp-sesman.service,chrome-remote-desktop@ubuntu.service,anydesk.service,NetworkManager.service,qemu-guest-agent.service,lightdm.service",
        )
    ).split(",")
    if name.strip()
]
SYSTEM_SERVICE_SPECS = [
    {"unit": "ssh.service", "name": "ssh", "patterns": ["/usr/sbin/sshd", "sshd: /usr/sbin/sshd -D"], "desc": "OpenBSD Secure Shell server"},
    {"unit": "xrdp.service", "name": "xrdp", "patterns": ["/usr/sbin/xrdp"], "desc": "xrdp daemon"},
    {"unit": "xrdp-sesman.service", "name": "xrdp-sesman", "patterns": ["/usr/sbin/xrdp-sesman"], "desc": "xrdp session manager"},
    {"unit": "chrome-remote-desktop@ubuntu.service", "name": "chrome-remote-desktop", "patterns": ["chrome-remote-desktop", "chrome-remote-desktop-host"], "desc": "Chrome Remote Desktop"},
    {"unit": "anydesk.service", "name": "anydesk", "patterns": ["/usr/bin/anydesk --service"], "desc": "AnyDesk"},
    {"unit": "NetworkManager.service", "name": "NetworkManager", "patterns": ["/usr/sbin/NetworkManager --no-daemon"], "desc": "Network Manager"},
    {"unit": "qemu-guest-agent.service", "name": "qemu-guest-agent", "patterns": ["/usr/sbin/qemu-ga"], "desc": "QEMU Guest Agent"},
    {"unit": "lightdm.service", "name": "lightdm", "patterns": ["/usr/sbin/lightdm"], "desc": "Light Display Manager"},
]

app.secret_key = env("AQUA_SECRET_KEY", "AQUA_DASHBOARD_SECRET")
# The package ships with a simple default so first-time installs can log in
# immediately after `install.sh`. Operators should still change this in `.env`
# before exposing the dashboard to a wider network.
ADMIN_PASSWORD = env("AQUA_ADMIN_PASSWORD", "123456789")

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


def run_capture(args, timeout=8, extra_env=None):
    """
    Structured command helper for tools we control directly.
    This avoids shell quoting issues and lets AQUA carry stable environment
    hints such as PM2_HOME when the dashboard itself runs under systemd.
    """
    env_map = os.environ.copy()
    if extra_env:
        env_map.update({str(key): str(value) for key, value in extra_env.items()})
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=env_map,
        )
        return (proc.stdout or "").strip()
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


def format_ts_ms(ts_ms):
    if not ts_ms:
        return ""
    try:
        return datetime.datetime.fromtimestamp(float(ts_ms) / 1000.0).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def gateway_parts():
    parsed = urlparse(GATEWAY_URL or "")
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    if parsed.port:
        port = parsed.port
    elif scheme == "https":
        port = 443
    else:
        port = 80
    return scheme, host, port


def public_dashboard_base_url():
    """
    Prefer an explicit public base URL for install-once/reuse-many scenarios.
    If it is missing, fall back to the current request host so the same build
    can still explain access correctly behind a reverse proxy.
    """
    if PUBLIC_BASE_URL:
        return PUBLIC_BASE_URL
    try:
        return request.host_url.rstrip("/")
    except RuntimeError:
        return f"http://127.0.0.1:{APP_PORT}"


def openclaw_tunnel_command():
    _, gateway_host, gateway_port = gateway_parts()
    if SSH_HOST and SSH_USER:
        return f"ssh -N -L {TUNNEL_LOCAL_PORT}:{gateway_host}:{gateway_port} -p {SSH_PORT} {SSH_USER}@{SSH_HOST}"
    return f"ssh -N -L {TUNNEL_LOCAL_PORT}:{gateway_host}:{gateway_port} -p <SSH_PORT> <SSH_USER>@<SSH_HOST>"


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


def format_duration(seconds):
    seconds = max(0, int(seconds or 0))
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


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


def parse_iso_datetime(value):
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None


def format_dt(dt):
    if not dt:
        return ""
    try:
        if dt.tzinfo is not None:
            dt = dt.astimezone()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


def token_runtime_snapshot():
    """
    Token cooldown / quota state is not stored in OpenClaw config.
    We derive it from recent journal lines plus auth-profiles usageStats and
    keep a short cache so the dashboard stays responsive while still surfacing
    near-real-time failures such as ChatGPT team-plan usage limits.
    """
    now = time.time()
    if TOKEN_RUNTIME_CACHE["value"] is not None and now - TOKEN_RUNTIME_CACHE["ts"] < TOKEN_RUNTIME_CACHE_TTL:
        return TOKEN_RUNTIME_CACHE["value"]

    usage_limit = {}
    usage_profiles = {}

    if os.path.exists(AUTH_PROFILES):
        try:
            data = json.loads(safe_read(AUTH_PROFILES) or "{}")
            usage_profiles = data.get("usageStats", {}) or {}
        except Exception:
            usage_profiles = {}

    journal = run_capture(
        ["journalctl", "--user", "-n", "400", "--no-pager", "-o", "short-iso"],
        timeout=10,
        extra_env=systemd_extra_env("user"),
    )
    limit_pattern = re.compile(r"Try again in\s*~?(\d+)\s*min", re.I)
    provider_pattern = re.compile(r"provider=([a-z0-9._-]+)", re.I)
    for raw_line in reversed((journal or "").splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        line_lower = line.lower()
        if "usage limit" not in line_lower and "rate limit" not in line_lower:
            continue
        provider_match = provider_pattern.search(line)
        provider = provider_match.group(1).strip().lower() if provider_match else "unknown"
        retry_match = limit_pattern.search(line)
        retry_after_min = int(retry_match.group(1)) if retry_match else None
        detected_at = parse_iso_datetime(line.split(" ", 1)[0])
        available_at = None
        if detected_at and retry_after_min is not None:
            available_at = detected_at + datetime.timedelta(minutes=retry_after_min)
        usage_limit[provider] = {
            "provider_key": provider,
            "state": "LIMITED",
            "label": "Bị giới hạn lượt dùng",
            "message": line.split("error=", 1)[-1].strip() if "error=" in line else line,
            "retry_after_min": retry_after_min,
            "detected_at": format_dt(detected_at),
            "available_at": format_dt(available_at),
            "is_active": bool(available_at and available_at > datetime.datetime.now(available_at.tzinfo)),
            "source": "journalctl --user",
        }
    snapshot = {"usage_profiles": usage_profiles, "usage_limit": usage_limit}
    TOKEN_RUNTIME_CACHE["ts"] = now
    TOKEN_RUNTIME_CACHE["value"] = snapshot
    return snapshot


def quota_risk_profile(status, usage_state, error_count, last_failure_at):
    """
    OpenClaw does not expose a numeric ChatGPT team-plan quota percentage.
    AQUA therefore publishes a clearly labeled heuristic risk level instead of
    inventing fake percentages. Hard lock state still maps to 0% usable.
    """
    text = f"{status or ''} {usage_state or ''}".lower()
    if "limited" in text:
        return {"label": "Đã chạm", "class": "critical", "usable_pct": 0}
    if int(error_count or 0) >= 3:
        return {"label": "Nguy cơ", "class": "high", "usable_pct": None}
    failure_dt = parse_iso_datetime(last_failure_at)
    if failure_dt:
        try:
            age_hours = (datetime.datetime.now(failure_dt.tzinfo) - failure_dt).total_seconds() / 3600.0
        except Exception:
            age_hours = None
        if age_hours is not None and age_hours <= 12:
            return {"label": "Nguy cơ", "class": "high", "usable_pct": None}
        if age_hours is not None and age_hours <= 36:
            return {"label": "Căng", "class": "medium", "usable_pct": None}
    if int(error_count or 0) >= 1:
        return {"label": "Căng", "class": "medium", "usable_pct": None}
    return {"label": "An toàn", "class": "low", "usable_pct": None}


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
    if any(token in sample for token in ["dbus", "dconf", "gvfs", "gnome-keyring", "gpg-agent", "pulseaudio", "at-spi", "evolution"]):
        return "Desktop / Session"
    if "dashboard" in sample:
        return "Dashboard"
    if "gateway" in sample or name == "bot":
        return "Gateway"
    if "assistant" in sample or "scheduler" in sample:
        return "Scheduler"
    if "watchdog" in sample:
        return "Watchdog"
    if "mission" in sample:
        return "Mission"
    return "Worker"


def read_proc_cmdline(pid):
    try:
        raw = open(f"/proc/{int(pid)}/cmdline", "rb").read().replace(b"\x00", b" ").decode("utf-8", "replace").strip()
        return raw
    except Exception:
        return ""


def read_proc_cwd(pid):
    try:
        return os.readlink(f"/proc/{int(pid)}/cwd")
    except Exception:
        return ""


def process_stats(pid):
    """
    Read lightweight runtime metrics for a live PID.
    We use `ps` here because it is available on standard Ubuntu VPS images and
    works for both PM2-managed processes and systemd user services.
    """
    if not pid:
        return {"cpu": 0.0, "mem_mb": 0.0, "uptime_s": 0}
    raw = run_capture(["ps", "-p", str(pid), "-o", "%cpu=,rss=,etimes="], timeout=5)
    if not raw:
        return {"cpu": 0.0, "mem_mb": 0.0, "uptime_s": 0}
    parts = raw.split()
    if len(parts) < 3:
        return {"cpu": 0.0, "mem_mb": 0.0, "uptime_s": 0}
    try:
        cpu = round(float(parts[0]), 1)
    except Exception:
        cpu = 0.0
    try:
        mem_mb = round(float(parts[1]) / 1024, 1)
    except Exception:
        mem_mb = 0.0
    try:
        uptime_s = int(float(parts[2]))
    except Exception:
        uptime_s = 0
    return {"cpu": cpu, "mem_mb": mem_mb, "uptime_s": uptime_s}


def ps_snapshot():
    raw = run_capture(["ps", "-eo", "pid=,ppid=,user=,stat=,comm=,args="], timeout=8)
    rows = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 5)
        if len(parts) < 6:
            continue
        pid_s, ppid_s, user, stat, comm, args = parts
        try:
            pid = int(pid_s)
        except Exception:
            pid = 0
        try:
            ppid = int(ppid_s)
        except Exception:
            ppid = 0
        rows.append({"pid": pid, "ppid": ppid, "user": user, "stat": stat, "comm": comm, "args": args})
    return rows


def extract_script_from_cmdline(cmdline):
    tokens = []
    try:
        tokens = shlex.split(str(cmdline or ""))
    except Exception:
        tokens = str(cmdline or "").split()
    for token in tokens:
        if token.endswith((".py", ".sh", ".js")):
            return token
    for token in tokens:
        if token.startswith("/") and os.path.exists(token):
            return token
    return ""


def systemctl_base(scope="user"):
    args = ["systemctl"]
    if scope == "user":
        args.append("--user")
    return args


def systemd_extra_env(scope="user"):
    """
    AQUA itself runs under a user service, so some VPSes do not expose the
    full interactive login environment to child `systemctl --user` calls.
    Supplying the standard user runtime bus paths keeps timer discovery
    consistent between SSH shells and the dashboard service.
    """
    if scope != "user":
        return None
    uid = os.getuid()
    runtime_dir = f"/run/user/{uid}"
    return {
        "XDG_RUNTIME_DIR": runtime_dir,
        "DBUS_SESSION_BUS_ADDRESS": f"unix:path={runtime_dir}/bus",
    }


def systemd_source_label(scope, unit_type):
    if scope == "user" and unit_type == "timer":
        return "Timer user"
    if scope == "user":
        return "Service user"
    if unit_type == "timer":
        return "System timer"
    return "System service"


def systemd_section_label(scope, unit_type):
    if scope == "user" and unit_type == "timer":
        return "Timer user"
    if scope == "user":
        return "Service user"
    if unit_type == "timer":
        return "System timer"
    return "System service"


def list_systemd_unit_files(scope="user", unit_type="service"):
    """
    Discover installed unit files, not just loaded/running ones.
    This is the key difference that lets AQUA show timers/services such as
    `nhiem-vu-quan-sat.service` even while they are currently inactive.
    """
    raw = run_capture(
        systemctl_base(scope) + ["list-unit-files", "--type", unit_type, "--plain", "--no-legend", "--no-pager"],
        timeout=8,
        extra_env=systemd_extra_env(scope),
    )
    items = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if not parts:
            continue
        unit = parts[0]
        if not unit.endswith(f".{unit_type}"):
            continue
        items[unit] = {
            "unit": unit,
            "unit_file_state": parts[1] if len(parts) > 1 else "",
            "vendor_preset": parts[2] if len(parts) > 2 else "",
        }
    return items


def list_systemd_loaded_units(scope="user", unit_type="service"):
    raw = run_capture(
        systemctl_base(scope) + ["list-units", "--all", "--type", unit_type, "--plain", "--no-legend", "--no-pager"],
        timeout=8,
        extra_env=systemd_extra_env(scope),
    )
    items = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 4)
        if len(parts) < 4:
            continue
        unit, load_state, active_state, sub_state = parts[:4]
        if not unit.endswith(f".{unit_type}"):
            continue
        items[unit] = {
            "unit": unit,
            "load_state": load_state,
            "active_state": active_state,
            "sub_state": sub_state,
            "description": parts[4] if len(parts) > 4 else unit,
        }
    return items


def list_systemd_triggers(scope="user"):
    """
    Build a reverse index of timer -> triggered service from currently loaded
    timers. Even if a service is inactive, this lets the UI explain why it
    exists and what wakes it up.
    """
    mapping = {}
    for unit_type in ("timer",):
        loaded = list_systemd_loaded_units(scope, unit_type)
        for name in loaded:
            detail = load_systemd_unit(name, scope=scope)
            if not detail:
                continue
            target = str(detail.get("Triggers") or "").strip()
            if target:
                mapping[target] = name
    return mapping


def service_names_from_systemd(scope="user"):
    args = ["systemctl"]
    if scope == "user":
        args.append("--user")
    args += ["list-units", "--type=service", "--state=running", "--plain", "--no-legend", "--no-pager"]
    raw = run_capture(args, timeout=8, extra_env=systemd_extra_env(scope))
    names = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        names.append(line.split(None, 1)[0])
    return names


def load_systemd_unit(name, scope="user"):
    args = systemctl_base(scope) + [
        "show",
        name,
        "--no-pager",
        "--property=Id,Description,MainPID,ActiveState,SubState,LoadState,UnitFileState,ExecMainStartTimestamp,ExecStart,FragmentPath,NRestarts,Triggers,TriggeredBy,NextElapseUSecRealtime,LastTriggerUSec,Names",
    ]
    raw = run_capture(args, timeout=8)
    if not raw:
        return None
    data = {}
    for line in raw.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value
    return data


def is_interesting_systemd_unit(name, unit_type, description=""):
    sample = normalize_text(f"{name} {description}")
    if unit_type == "timer":
        return True
    needles = [
        "openclaw",
        "aqua",
        "assistant",
        "watchdog",
        "nhiem-vu",
        "mission",
        "scheduler",
        "dashboard",
        "gateway",
    ]
    return any(needle in sample for needle in needles)


def file_stat_summary(path):
    if not path or not os.path.exists(path):
        return {"size_bytes": 0, "size_human": "0 B", "updated_at": ""}
    try:
        stat = os.stat(path)
    except OSError:
        return {"size_bytes": 0, "size_human": "0 B", "updated_at": ""}
    return {
        "size_bytes": stat.st_size,
        "size_human": human_size(stat.st_size),
        "updated_at": format_ts(stat.st_mtime),
    }


def systemd_unit_inventory(scope="user", unit_type="service"):
    """
    Return one normalized task inventory for systemd units.
    We merge `list-unit-files` with `list-units --all` so AQUA sees both
    installed-but-inactive tasks and currently loaded/active tasks.
    """
    unit_files = list_systemd_unit_files(scope, unit_type)
    loaded_units = list_systemd_loaded_units(scope, unit_type)
    reverse_triggers = list_systemd_triggers(scope) if unit_type == "service" else {}
    items = []
    for unit_name in sorted(set(unit_files) | set(loaded_units)):
        unit_file = unit_files.get(unit_name, {})
        loaded = loaded_units.get(unit_name, {})
        detail = None
        if unit_type == "timer" or is_interesting_systemd_unit(unit_name, unit_type, loaded.get("description", "")):
            detail = load_systemd_unit(unit_name, scope=scope) or {}
        detail = detail or {}
        pid = 0
        if unit_type == "service":
            try:
                pid = int(detail.get("MainPID") or 0)
            except Exception:
                pid = 0
        stats = process_stats(pid)
        cmdline = read_proc_cmdline(pid) if pid else ""
        cwd = read_proc_cwd(pid) if pid else ""
        script = extract_script_from_cmdline(cmdline)
        fragment_path = str(detail.get("FragmentPath") or "")
        file_info = file_stat_summary(script if script and os.path.exists(script) else fragment_path)
        name = unit_name.rsplit(".", 1)[0]
        description = detail.get("Description") or loaded.get("description") or unit_name
        load_state = detail.get("LoadState") or loaded.get("load_state") or ("loaded" if unit_file else "not-found")
        active_state = detail.get("ActiveState") or loaded.get("active_state") or "inactive"
        sub_state = detail.get("SubState") or loaded.get("sub_state") or ("waiting" if unit_type == "timer" and active_state == "active" else "")
        unit_file_state = detail.get("UnitFileState") or unit_file.get("unit_file_state") or ""
        triggers = str(detail.get("Triggers") or "").strip()
        triggered_by = str(detail.get("TriggeredBy") or "").strip() or reverse_triggers.get(unit_name, "")
        item = {
            "id": f"systemd:{scope}:{unit_type}:{unit_name}",
            "name": name,
            "group": detect_process_group(name, f"{description} {script or fragment_path}"),
            "section": systemd_section_label(scope, unit_type),
            "importance": detect_importance(f"{unit_name} {description} {triggers} {triggered_by}", fallback="medium"),
            "status": sub_state or active_state or unit_file_state or load_state or "unknown",
            "active_state": active_state,
            "sub_state": sub_state,
            "load_state": load_state,
            "unit_file_state": unit_file_state or "unknown",
            "vendor_preset": unit_file.get("vendor_preset", ""),
            "pid": pid,
            "uptime": format_duration(stats.get("uptime_s")),
            "restarts": int(detail.get("NRestarts") or 0) if str(detail.get("NRestarts") or "").isdigit() else 0,
            "cpu": stats.get("cpu", 0.0),
            "mem_mb": stats.get("mem_mb", 0.0),
            "script": script or cmdline or fragment_path or unit_name,
            "script_name": os.path.basename(script or fragment_path) if (script or fragment_path) else unit_name,
            "script_size": file_info["size_human"],
            "script_size_bytes": file_info["size_bytes"],
            "script_updated_at": file_info["updated_at"],
            "cwd": cwd,
            "interpreter": "",
            "exec_mode": unit_type,
            "desc": description,
            "steps": [],
            "step_count": 0,
            "line_count": 0,
            "source": f"systemd-{scope}",
            "source_label": systemd_source_label(scope, unit_type),
            "unit": unit_name,
            "manager": "systemd",
            "unit_type": unit_type,
            "unit_type_label": "Timer" if unit_type == "timer" else "Service",
            "scope": scope,
            "scope_label": "User" if scope == "user" else "System",
            "fragment_path": fragment_path,
            "triggers": triggers,
            "triggered_by": triggered_by,
            "next_run": str(detail.get("NextElapseUSecRealtime") or "").strip(),
            "last_run": str(detail.get("LastTriggerUSec") or "").strip(),
            "important_system": scope == "system" and unit_name in SYSTEM_SERVICE_ALLOWLIST,
        }
        items.append(item)
    return items


def user_service_to_mission(service_name):
    data = load_systemd_unit(service_name, scope="user")
    if not data:
        return None
    try:
        pid = int(data.get("MainPID") or 0)
    except Exception:
        pid = 0
    cmdline = read_proc_cmdline(pid)
    script = extract_script_from_cmdline(cmdline)
    cwd = read_proc_cwd(pid)
    stats = process_stats(pid)
    desc = data.get("Description", "") or service_name
    updated_at = ""
    script_size = 0
    line_count = 0
    steps = []
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
    status = data.get("SubState") or data.get("ActiveState") or "unknown"
    return {
        "id": service_name,
        "name": service_name.removesuffix(".service"),
        "group": detect_process_group(service_name, f"{script} {desc}"),
        "importance": detect_importance(f"{service_name} {desc} {script}", fallback="medium"),
        "status": status,
        "pid": pid,
        "uptime": format_duration(stats.get("uptime_s")),
        "restarts": int(data.get("NRestarts") or 0) if str(data.get("NRestarts") or "").isdigit() else 0,
        "cpu": stats.get("cpu", 0.0),
        "mem_mb": stats.get("mem_mb", 0.0),
        "script": script or cmdline or data.get("ExecStart", ""),
        "script_name": os.path.basename(script) if script else (cmdline.split()[0] if cmdline else service_name),
        "script_size": human_size(script_size),
        "script_size_bytes": script_size,
        "script_updated_at": updated_at,
        "cwd": cwd,
        "interpreter": "",
        "exec_mode": "service",
        "desc": desc,
        "steps": steps[:12],
        "step_count": len(steps),
        "line_count": line_count,
        "source": "systemd-user",
        "source_label": "Service user",
        "unit": service_name,
        "manager": "systemd",
    }


def system_service_to_mission(service_name):
    data = load_systemd_unit(service_name, scope="system")
    if not data:
        return None
    try:
        pid = int(data.get("MainPID") or 0)
    except Exception:
        pid = 0
    cmdline = read_proc_cmdline(pid)
    script = extract_script_from_cmdline(cmdline)
    cwd = read_proc_cwd(pid)
    stats = process_stats(pid)
    desc = data.get("Description", "") or service_name
    status = data.get("SubState") or data.get("ActiveState") or "unknown"
    return {
        "id": service_name,
        "name": service_name.removesuffix(".service"),
        "group": "System service",
        "importance": detect_importance(f"{service_name} {desc} {cmdline}", fallback="medium"),
        "status": status,
        "pid": pid,
        "uptime": format_duration(stats.get("uptime_s")),
        "restarts": int(data.get("NRestarts") or 0) if str(data.get("NRestarts") or "").isdigit() else 0,
        "cpu": stats.get("cpu", 0.0),
        "mem_mb": stats.get("mem_mb", 0.0),
        "script": script or cmdline or data.get("ExecStart", ""),
        "script_name": os.path.basename(script) if script else (cmdline.split()[0] if cmdline else service_name),
        "script_size": human_size(0),
        "script_size_bytes": 0,
        "script_updated_at": "",
        "cwd": cwd,
        "interpreter": "",
        "exec_mode": "service",
        "desc": desc,
        "steps": [],
        "step_count": 0,
        "line_count": 0,
        "source": "systemd-system",
        "source_label": "System service",
        "unit": service_name,
        "manager": "systemd",
    }


def important_system_service_missions():
    """
    Use `ps` as the primary signal for important OS services.
    This is more reliable inside the dashboard service context than depending
    on `systemctl` DBus access from within the web process.
    """
    rows = ps_snapshot()
    items = []
    for spec in SYSTEM_SERVICE_SPECS:
        if spec["unit"] not in SYSTEM_SERVICE_ALLOWLIST:
            continue
        row = None
        for candidate in rows:
            hay = f"{candidate.get('comm','')} {candidate.get('args','')}"
            if any(pattern in hay for pattern in spec["patterns"]):
                row = candidate
                break
        if not row:
            continue
        pid = row.get("pid", 0)
        stats = process_stats(pid)
        items.append(
            {
                "id": spec["unit"],
                "name": spec["name"],
                "group": "System service",
                "importance": detect_importance(f"{spec['unit']} {spec['name']} {spec['desc']}", fallback="medium"),
                "status": "running",
                "pid": pid,
                "uptime": format_duration(stats.get("uptime_s")),
                "restarts": 0,
                "cpu": stats.get("cpu", 0.0),
                "mem_mb": stats.get("mem_mb", 0.0),
                "script": row.get("args", ""),
                "script_name": row.get("comm", ""),
                "script_size": human_size(0),
                "script_size_bytes": 0,
                "script_updated_at": "",
                "cwd": "",
                "interpreter": "",
                "exec_mode": "service",
                "desc": spec["desc"],
                "steps": [],
                "step_count": 0,
                "line_count": 0,
                "source": "systemd-system",
                "source_label": "System service",
                "unit": spec["unit"],
                "manager": "systemd",
            }
        )
    return items


def load_pm2_processes():
    raw = run_capture([PM2_BIN, "jlist"], timeout=8, extra_env={"PM2_HOME": PM2_HOME})
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []


def runtime_processes():
    """
    Build one operational inventory from PM2 and systemd.
    Unlike the earlier runtime-only view, this inventory also includes
    installed but inactive timers/services so recurring tasks are still
    visible before their next run.
    """
    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    items = []
    seen = set()

    def seen_key(item):
        if item.get("source") == "pm2":
            return ("pm2", item.get("id"))
        return (item.get("source"), item.get("unit") or item.get("name"), item.get("unit_type"))

    for proc in load_pm2_processes():
        pm_env = proc.get("pm2_env", {})
        script = pm_env.get("pm_exec_path", "")
        uptime_ms = pm_env.get("pm_uptime", 0)
        uptime_s = max(0, (now_ms - uptime_ms) // 1000) if uptime_ms else 0
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

        name = proc.get("name", "")
        item = {
            "id": f"pm2:{proc.get('pm_id')}",
            "name": name,
            "group": detect_process_group(name, script),
            "section": detect_process_group(name, script),
            "importance": detect_importance(f"{name} {script}", fallback="medium"),
            "status": pm_env.get("status", "unknown"),
            "active_state": pm_env.get("status", "unknown"),
            "sub_state": pm_env.get("status", "unknown"),
            "load_state": "loaded",
            "unit_file_state": "",
            "pid": proc.get("pid", 0),
            "uptime": format_duration(uptime_s),
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
            "desc": desc or name,
            "steps": steps[:12],
            "step_count": len(steps),
            "line_count": line_count,
            "source": "pm2",
            "source_label": "PM2",
            "unit": "",
            "manager": "pm2",
            "unit_type": "process",
            "unit_type_label": "Process",
            "scope": "user",
            "scope_label": "User",
            "fragment_path": "",
            "triggers": "",
            "triggered_by": "",
            "next_run": "",
            "last_run": "",
            "important_system": False,
        }
        items.append(item)
        seen.add(seen_key(item))

    for item in systemd_unit_inventory(scope="user", unit_type="service") + systemd_unit_inventory(scope="user", unit_type="timer"):
        key = seen_key(item)
        if key in seen:
            continue
        items.append(item)
        seen.add(key)

    for item in systemd_unit_inventory(scope="system", unit_type="service") + systemd_unit_inventory(scope="system", unit_type="timer"):
        if not item:
            continue
        key = seen_key(item)
        if key in seen:
            continue
        items.append(item)
        seen.add(key)

    return sorted(items, key=lambda item: (item.get("section", ""), item.get("unit_type", ""), item.get("name", "")))


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
                "allowed_chat_count": len(allowed_chats),
                "groups": group_keys,
                "groups_count": len(group_keys),
                "group_policy": snap_tg.get("groupPolicy", ""),
                "dm_policy": snap_tg.get("dmPolicy", ""),
            }
        )
        for chat_id in allowed_chats:
            add_telegram_candidate(
                candidates,
                chat_id,
                f"snapshot/{os.path.basename(path)}",
                role="Schema cũ / allowedChats",
                current=False,
                excerpt=f"allowedChats: {', '.join(allowed_chats[:6])}",
                kind=telegram_chat_kind(chat_id),
            )

    actors = sorted(
        [
            {
                **item,
                "kind_label": "User / DM" if item.get("kind") == "user" else "Nhóm" if item.get("kind") == "group" else "Mặc định" if item.get("kind") == "default" else "Khác",
                "source_count": len(item.get("sources", [])),
            }
            for item in candidates.values()
        ],
        key=lambda item: (
            0 if item.get("current") else 1,
            0 if item.get("kind") == "user" else 1 if item.get("kind") == "group" else 2,
            item.get("id", ""),
        ),
    )

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
        output = cached.get("raw_output", "")
        url = cached.get("dashboard_url", "")
        base_url = cached.get("base_url", "")
        token = cached.get("token", "")
    else:
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
        OPENCLAW_ACCESS_CACHE["ts"] = now
        OPENCLAW_ACCESS_CACHE["value"] = {
            "ok": bool(url),
            "dashboard_url": url,
            "base_url": base_url,
            "token": token,
            "raw_output": output[-4000:],
        }
    _, gateway_host, gateway_port = gateway_parts()
    public_url = public_dashboard_base_url()
    result = {
        "ok": bool(url),
        "dashboard_url": url,
        "base_url": base_url,
        "token": token,
        "gateway_url": GATEWAY_URL,
        "gateway_host": gateway_host,
        "gateway_port": gateway_port,
        "tunnel_local_port": TUNNEL_LOCAL_PORT,
        "tunnel_command": openclaw_tunnel_command(),
        "local_open": f"http://127.0.0.1:{TUNNEL_LOCAL_PORT}/",
        "public_proxy_url": f"{public_url}/openclaw/",
        "public_dashboard_url": f"{public_url}/",
        "reason_public": "Đường public /openclaw/ chỉ đi qua Flask proxy HTTP và không phải đường truy cập chuẩn cho WebSocket + token của OpenClaw.",
        "reason_root": f"Mở root 127.0.0.1:{TUNNEL_LOCAL_PORT} chỉ hiện màn Connect; muốn vào thẳng phải dùng URL có #token do openclaw dashboard sinh ra.",
        "raw_output": output[-4000:],
    }
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
    runtime = token_runtime_snapshot()
    usage_profiles = runtime.get("usage_profiles", {})
    usage_limits = runtime.get("usage_limit", {})
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
                profile_usage = usage_profiles.get(key, {}) or {}
                provider_usage = usage_limits.get(str(prof.get("provider") or "").strip().lower(), {}) or {}
                total_days = round((exp - iat) / 86400, 1) if exp and iat and exp > iat else None
                exp_date = datetime.datetime.fromtimestamp(exp).strftime("%Y-%m-%d %H:%M:%S") if exp else "Unknown"
                issued_date = datetime.datetime.fromtimestamp(iat).strftime("%Y-%m-%d %H:%M:%S") if iat else None
                days_left = round((exp - now) / 86400, 1) if exp else -1
                pct_left = round(max(0, min(100, (days_left / total_days) * 100)), 1) if total_days and total_days > 0 else None
                status = "EXPIRED" if days_left < 0 else "WARNING" if days_left < 2 else "ACTIVE"
                priority = "critical" if days_left < 1 else "high" if days_left < 3 else "medium"
                usage_state = str(provider_usage.get("state") or "").upper()
                if usage_state == "LIMITED" and provider_usage.get("is_active"):
                    status = "LIMITED"
                    priority = "critical"
                last_failure_at = format_ts_ms(profile_usage.get("lastFailureAt"))
                risk = quota_risk_profile(status, usage_state, int(profile_usage.get("errorCount") or 0), last_failure_at)
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
                        "email": prof.get("email"),
                        "usage_state": usage_state or "NORMAL",
                        "usage_label": provider_usage.get("label") or "Bình thường",
                        "usage_message": provider_usage.get("message") or "",
                        "retry_after_min": provider_usage.get("retry_after_min"),
                        "limit_detected_at": provider_usage.get("detected_at") or "",
                        "available_at": provider_usage.get("available_at") or "",
                        "runtime_source": provider_usage.get("source") or "",
                        "last_used_at": format_ts_ms(profile_usage.get("lastUsed")),
                        "last_failure_at": last_failure_at,
                        "error_count": int(profile_usage.get("errorCount") or 0),
                        "quota_risk": risk.get("label"),
                        "quota_risk_class": risk.get("class"),
                        "quota_usable_pct": risk.get("usable_pct"),
                    }
                )
        except Exception:
            pass
    return jsonify(tokens)


@app.route("/api/logs/openclaw")
@login_required
def get_openclaw_logs():
    targets = [
        {"name": "bot", "service_name": "openclaw-gateway.service"},
        {"name": "GodMode_Mission", "service_name": ""},
        {"name": "assistant_scheduler", "service_name": "assistant-scheduler.service"},
        {"name": "aqua_dashboard", "service_name": "aqua-dashboard.service"},
    ]
    service_map = {
        "bot": "openclaw-gateway.service",
        "assistant_scheduler": "assistant-scheduler.service",
        "aqua_dashboard": "aqua-dashboard.service",
    }
    raw = run_capture([PM2_BIN, "jlist"], timeout=8, extra_env={"PM2_HOME": PM2_HOME})
    proc_map = {}
    try:
        for proc in json.loads(raw or "[]"):
            proc_map[proc.get("name")] = proc.get("pm2_env", {})
    except Exception:
        proc_map = {}
    items = []
    for target in targets:
        name = target["name"]
        service_name = target["service_name"] or service_map.get(name) or ""
        env = proc_map.get(name, {})
        source_label = "PM2"
        out_lines = tail_lines(env.get("pm_out_log_path", ""), 12)
        err_lines = tail_lines(env.get("pm_err_log_path", ""), 12)
        if service_name and not (out_lines or err_lines):
            source_label = "Service user"
            unit_log = run_capture(["journalctl", "--user", "-u", service_name, "-n", "12", "--no-pager", "-o", "short-iso"], timeout=8)
            out_lines = [line for line in unit_log.splitlines() if line.strip()]
        last_line = (err_lines[-1] if err_lines else out_lines[-1] if out_lines else "").strip()
        items.append(
            {
                "name": name,
                "out_lines": out_lines,
                "error_lines": err_lines,
                "last_line": last_line,
                "error_count": len(err_lines),
                "has_activity": bool(out_lines or err_lines),
                "source_label": source_label,
                "unit": service_name or "",
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
    return jsonify(runtime_processes())


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
