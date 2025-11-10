import re
from datetime import datetime
from pathlib import Path


def tz_no_colon(tz: str) -> str:
    m = re.match(r"^([+-]\d{2}):?(\d{2})$", tz)
    if m:
        return f"{m.group(1)}{m.group(2)}"
    return tz

def now_parts() -> tuple[str, str]:
    now = datetime.now().astimezone()
    return now.strftime("%H:%M"), tz_no_colon(now.strftime("%z"))


def update_file(path: Path, now_time: str, now_tz: str) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False

    def repl(m: re.Match[str]) -> str:
        prefix = m.group(1)
        date = m.group(2)
        hh = m.group(3)
        mm = m.group(4)
        tz = m.group(5)
        tail = m.group(6) or ""

        if not hh:
            hhmm = now_time
        else:
            hhmm = f"{hh}:{mm}"

        if not tz:
            z = now_tz
        else:
            z = tz_no_colon(tz)
        return f"{prefix}{date} {hhmm} {z}{tail}"

    pattern = re.compile(
        r"^(Date:\s*)"  # 1 prefix
        r"(\d{4}-\d{2}-\d{2})"  # 2 date
        r"(?:\s+(\d{2}):(\d{2}))?"  # 3,4 time optional
        r"(?:\s+([+-]\d{2}:?\d{2}))?"  # 5 tz optional
        r"(.*)$",  # 6 tail
        re.MULTILINE,
    )
    new_text, n = pattern.subn(repl, text)
    if n and new_text != text:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        return True
    return False


def main() -> int:
    docs_dir = Path("docs")
    if not docs_dir.exists():
        return 0
    now_time, now_tz = now_parts()
    exts = {".md", ".txt"}
    changed = []
    for p in docs_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            if update_file(p, now_time, now_tz):
                changed.append(p)

    # Print a concise summary to stdout
    if changed:
        print("Updated Date lines in:")
        for p in changed:
            print(f" - {p}")
    else:
        print("No Date lines required updates.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
