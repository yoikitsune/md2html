import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional


_RECENT_UPDATES: Optional[List[dict]] = None


def _find_git_root(start_path: str) -> Optional[str]:
    path = os.path.abspath(start_path)
    while True:
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def _git_root_from_git(docs_dir: str) -> Optional[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", os.path.abspath(docs_dir), "rev-parse", "--show-toplevel"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError:
        return None

    if proc.returncode != 0:
        return None

    root = (proc.stdout or "").strip()
    return root or None


def _resolve_git_root(docs_dir: str) -> Optional[str]:
    return _git_root_from_git(docs_dir) or _find_git_root(docs_dir)


def _git_latest_commits(git_root: str, docs_dir: str) -> Dict[str, dict]:
    """Return map of file path (relative to git_root) to latest commit metadata."""
    docs_rel = os.path.relpath(os.path.abspath(docs_dir), os.path.abspath(git_root))

    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                git_root,
                "log",
                "--name-only",
                "--pretty=format:%ct%x1f%an",
                "--",
                docs_rel,
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except OSError:
        return {}

    if proc.returncode != 0:
        return {}

    latest: Dict[str, dict] = {}
    current_ts: Optional[int] = None
    current_author: Optional[str] = None

    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if "\x1f" in line:
            ts_str, author = line.split("\x1f", 1)
            if ts_str.isdigit():
                try:
                    current_ts = int(ts_str)
                except ValueError:
                    current_ts = None
                current_author = author.strip() or None
                continue

        if current_ts is None:
            continue

        if not line.endswith(".md"):
            continue

        if not (line == docs_rel or line.startswith(docs_rel + os.sep)):
            continue

        if line not in latest:
            latest[line] = {
                "ts": current_ts,
                "author": current_author,
            }

    return latest


def _format_date(ts: int) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _extract_title_from_markdown(abs_src_path: str) -> Optional[str]:
    try:
        with open(abs_src_path, "r", encoding="utf-8", errors="replace") as f:
            lines = []
            for _ in range(250):
                line = f.readline()
                if not line:
                    break
                lines.append(line.rstrip("\n"))
    except OSError:
        return None

    in_front_matter = False
    in_code_fence = False
    front_matter_done = False

    for i, raw in enumerate(lines):
        line = raw.rstrip()

        if i == 0 and line.strip() == "---":
            in_front_matter = True
            continue

        if in_front_matter:
            if line.strip() == "---":
                in_front_matter = False
                front_matter_done = True
            continue

        if not front_matter_done and line.strip() == "":
            continue

        if line.strip().startswith("```") or line.strip().startswith("~~~"):
            in_code_fence = not in_code_fence
            continue

        if in_code_fence:
            continue

        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            title = m.group(1).strip()
            return title or None

    return None


def on_nav(nav, config, files):
    global _RECENT_UPDATES

    docs_dir = config.get("docs_dir")
    if not docs_dir:
        _RECENT_UPDATES = []
        config.extra["recent_updates"] = []
        return nav

    git_root = _resolve_git_root(docs_dir)
    commit_by_file: Dict[str, dict] = {}
    if git_root:
        commit_by_file = _git_latest_commits(git_root, docs_dir)

    items: List[dict] = []

    docs_dir_abs = os.path.abspath(docs_dir)

    for page in nav.pages:
        if not getattr(page, "file", None):
            continue
        src_path = getattr(page.file, "src_path", "")
        if not src_path.endswith(".md"):
            continue
        if src_path == "index.md":
            continue

        abs_src = getattr(page.file, "abs_src_path", None)
        if not abs_src or not os.path.exists(abs_src):
            continue

        ts: Optional[int] = None
        author: Optional[str] = None

        if git_root:
            try:
                rel_to_git = os.path.relpath(os.path.abspath(abs_src), os.path.abspath(git_root))
                commit = commit_by_file.get(rel_to_git)
                if commit:
                    ts = commit.get("ts")
                    author = commit.get("author")
            except ValueError:
                ts = None

        if git_root and ts is None:
            continue

        if ts is None:
            try:
                ts = int(os.path.getmtime(abs_src))
            except OSError:
                continue

        title = _extract_title_from_markdown(abs_src) or getattr(page, "title", None)
        if not title:
            base = os.path.basename(abs_src)
            if base.lower() in {"readme.md", "index.md"}:
                title = os.path.basename(os.path.dirname(abs_src))
            else:
                title = os.path.splitext(base)[0]

        try:
            full_path = os.path.relpath(os.path.abspath(abs_src), docs_dir_abs)
        except ValueError:
            full_path = src_path

        items.append(
            {
                "title": title,
                "url": page.url,
                "ts": ts,
                "path": full_path,
                "author": author,
            }
        )

    items.sort(key=lambda x: x["ts"], reverse=True)
    items = items[:5]

    _RECENT_UPDATES = items
    config.extra["recent_updates"] = [
        {
            "title": it["title"],
            "url": it["url"],
            "date": _format_date(it["ts"]),
            "path": it.get("path") or "",
            "author": it.get("author") or "",
        }
        for it in items
    ]

    return nav


def _build_recent_updates_block(recent_updates: List[dict]) -> str:
    lines = ['!!! info "Dernières mises à jour"']
    for it in recent_updates:
        title = it.get("title") or "(sans titre)"
        url = it.get("url") or "#"
        date = it.get("date") or ""
        path = it.get("path") or ""
        suffix = f" — `{date}`" if date else ""
        if path:
            lines.append(f"    - [{title}]({url}){suffix}\n      `/{path}`")
        else:
            lines.append(f"    - [{title}]({url}){suffix}")
    return "\n".join(lines)


def _insert_after_title(markdown: str, block: str) -> str:
    lines = markdown.splitlines(True)
    for i, line in enumerate(lines):
        if re.match(r"^#\\s+", line):
            insert_at = i + 1
            if insert_at < len(lines) and lines[insert_at].strip() == "":
                insert_at += 1
            block_text = block
            if not block_text.endswith("\n"):
                block_text += "\n"
            block_text += "\n"
            lines.insert(insert_at, block_text)
            return "".join(lines)

    return block + "\n\n" + markdown


def on_page_markdown(markdown, page, config, files):
    if not getattr(page, "file", None):
        return markdown

    if getattr(page.file, "src_path", "") != "index.md":
        return markdown

    page.meta["template"] = "home.html"

    return markdown
