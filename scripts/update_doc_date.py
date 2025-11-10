import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_staged_files() -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"],
            text=True,
        )
    except Exception:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def tz_no_colon(tz: str) -> str:
    # Convert -05:00 -> -0500; leave already normalized as-is
    m = re.match(r"^([+-]\d{2}):?(\d{2})$", tz)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return tz


def update_date_lines(path: Path, now_time_part: str, now_tz: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False

    # Normalize three cases:
    # 1) Bare date -> add current HH:MM and tz
    # 2) Date + time no tz -> add current tz
    # 3) Date + time + tz with colon -> normalize tz to no-colon

    def repl(match: re.Match[str]) -> str:
        prefix = match.group(1)
        date = match.group(2)
        hh = match.group(3)
        mm = match.group(4)
        tz = match.group(5)
        tail = match.group(6) or ""

        if not hh:
            hhmm = now_time_part
        else:
            hhmm = f"{hh}:{mm}"

        if not tz:
            tz_fmt = now_tz
        else:
            tz_fmt = tz_no_colon(tz)

        return f"{prefix}{date} {hhmm} {tz_fmt}{tail}"

    pattern = re.compile(
        r"^(Date:\s*)"  # 1 prefix
        r"(\d{4}-\d{2}-\d{2})"  # 2 date
        r"(?:\s+(\d{2}):(\d{2}))?"  # 3,4 time optional
        r"(?:\s+([+-]\d{2}:?\d{2}))?"  # 5 tz optional (with or without colon)
        r"(.*)$",  # 6 rest of line
        re.MULTILINE,
    )

    new_text, n = pattern.subn(repl, text)
    if n and new_text != text:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        return True
    return False


def git_add(path: Path) -> None:
    try:
        subprocess.check_call(["git", "add", str(path)])
    except Exception:
        pass


def main() -> int:
    staged = get_staged_files()
    if not staged:
        return 0

    targets = [
        Path(p)
        for p in staged
        if p.startswith("docs/") and Path(p).suffix.lower() in {".md", ".txt"}
    ]
    if not targets:
        return 0

    # Current time and tz used when missing in lines
    now = datetime.now().astimezone()
    time_part = now.strftime("%H:%M")
    tz_part = tz_no_colon(now.strftime("%z"))
    updated_any = False
    for path in targets:
        if path.exists() and update_date_lines(path, time_part, tz_part):
            git_add(path)
            updated_any = True

    # Be quiet; always allow commit to continue
    return 0


if __name__ == "__main__":
    sys.exit(main())
