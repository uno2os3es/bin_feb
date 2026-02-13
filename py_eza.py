#!/data/data/com.termux/files/usr/bin/env python3
import argparse
import datetime
import grp
import json
import os
import pwd
import shutil
import stat
import subprocess

# ------------------------------------------------------------
# Color + icon helpers
# ------------------------------------------------------------


def colorize(
    text: str,
    mode: int,
    link_target: str | None = None,
) -> str:
    # Minimal LS-like coloring
    if stat.S_ISDIR(mode):
        return f"\033[34;1m{text}\033[0m"
    if stat.S_ISLNK(mode):
        return f"\033[36m{text}\033[0m"
    if mode & stat.S_IXUSR:
        return f"\033[32m{text}\033[0m"
    return text


def detect_icon(name: str, mode: int) -> str:
    if stat.S_ISDIR(mode):
        return "📁"
    if stat.S_ISLNK(mode):
        return "🔗"
    ext = name.lower().split(".")[-1]
    if ext in (
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
    ):
        return "🖼️"
    if ext in ("py", "sh"):
        return "🐍"
    if ext in ("zip", "tar", "gz", "bz2", "xz"):
        return "📦"
    return "📄"


# ------------------------------------------------------------
# Git support — porcelain v2, NUL-separated
# ------------------------------------------------------------


def get_git_status_for_dir(
    path: str,
) -> dict[str, dict[str, str]]:
    """Return {filename: {"index": X, "work": Y, "raw": XY}}."""
    try:
        p = subprocess.run(
            [
                "git",
                "-C",
                path,
                "status",
                "--porcelain=v2",
                "-z",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=False,
            check=False,
        )
    except FileNotFoundError:
        return {}

    out = p.stdout
    result = {}

    records = out.split(b"\x00")

    for rec in records:
        if not rec.startswith(b"1 "):
            continue
        parts = rec.split(b" ")
        if len(parts) < 8:
            continue

        xy = parts[1].decode("utf-8")
        x, y = xy[0], xy[1]
        filename = parts[-1].decode("utf-8", errors="ignore")

        result[filename] = {
            "index": x,
            "work": y,
            "raw": xy,
        }

    return result


# ------------------------------------------------------------
# Entry container
# ------------------------------------------------------------


class Entry:

    def __init__(
        self,
        path: str,
        name: str,
        stat_obj,
        link_target=None,
        git=None,
    ) -> None:
        self.path = path
        self.name = name
        self.stat = stat_obj
        self.link_target = link_target
        self.git = git


# ------------------------------------------------------------
# Formatting
# ------------------------------------------------------------


def mode_to_string(mode: int) -> str:
    chars = []
    chars.append("d" if stat.S_ISDIR(mode) else "l" if stat.S_ISLNK(mode) else "-")
    perms = [
        (stat.S_IRUSR, "r"),
        (stat.S_IWUSR, "w"),
        (stat.S_IXUSR, "x"),
        (stat.S_IRGRP, "r"),
        (stat.S_IWGRP, "w"),
        (stat.S_IXGRP, "x"),
        (stat.S_IROTH, "r"),
        (stat.S_IWOTH, "w"),
        (stat.S_IXOTH, "x"),
    ]
    for bit, ch in perms:
        chars.append(ch if (mode & bit) else "-")
    return "".join(chars)


def human_size(n: int) -> str:
    for unit in ["B", "K", "M", "G", "T"]:
        if n < 1024:
            return f"{n}{unit}"
        n /= 1024
    return f"{n:.1f}P"


# ------------------------------------------------------------
# Long output
# ------------------------------------------------------------


def output_long(
    entries: list[Entry],
    icons=False,
    colors=True,
    human=True,
) -> None:
    for e in entries:
        st = e.stat
        mode_s = mode_to_string(st.st_mode)

        nlink = st.st_nlink
        user = pwd.getpwuid(st.st_uid).pw_name
        group = grp.getgrgid(st.st_gid).gr_name

        size = human_size(st.st_size) if human else str(st.st_size)

        mtime = datetime.datetime.fromtimestamp(st.st_mtime)
        tstr = mtime.strftime("%Y-%m-%d %H:%M")

        name = e.name
        if icons:
            name = f"{detect_icon(e.name, st.st_mode)} {name}"
        if colors:
            name = colorize(name, st.st_mode, e.link_target)

        # Add git mark at end
        gitmark = ""
        if e.git:
            gitmark = f" {e.git['raw']}"

        print(f"{mode_s} {nlink:2} {user:8} {group:8} {size:>6} {tstr} {name}{gitmark}")


# ------------------------------------------------------------
# Two-column output (auto-width)
# ------------------------------------------------------------


def output_columns(
    entries: list[Entry],
    icons=False,
    colors=True,
    width=None,
) -> None:
    # Determine width
    if width is None:
        env_cols = os.environ.get("COLUMNS")
        if env_cols and env_cols.isdigit():
            width = int(env_cols)
        else:
            try:
                width = shutil.get_terminal_size().columns
            except Exception:
                width = 48  # Termux fallback

    width = max(20, width)
    cols = 2
    col_width = width // cols

    def real_len(s: str) -> int:
        import regex as re

        return len(re.sub(r"\x1b\[[0-9;]*m", "", s))

    def truncate(text: str, max_len: int) -> str:
        if real_len(text) <= max_len:
            return text
        import regex as re

        plain = re.sub(r"\x1b\[[0-9;]*m", "", text)
        return plain[: max_len - 1] + "…"

    rendered = []
    for e in entries:
        txt = e.name
        if icons:
            txt = f"{detect_icon(e.name, e.stat.st_mode)} {txt}"
        if colors:
            txt = colorize(txt, e.stat.st_mode, e.link_target)
        txt = truncate(txt, col_width - 1)
        rendered.append(txt)

    for i in range(0, len(rendered), cols):
        row = rendered[i : i + cols]
        padded = [r + " " * (col_width - real_len(r)) for r in row]
        print("".join(padded))


# ------------------------------------------------------------
# Tree view
# ------------------------------------------------------------


def print_tree(
    base: str,
    prefix: str = "",
    icons=False,
    colors=True,
) -> None:
    try:
        names = sorted(os.listdir(base))
    except PermissionError:
        print(prefix + " [permission denied]")
        return

    for i, name in enumerate(names):
        path = os.path.join(base, name)
        is_last = i == len(names) - 1
        connector = "└── " if is_last else "├── "

        try:
            st = os.lstat(path)
        except FileNotFoundError:
            continue

        txt = name
        if icons:
            txt = f"{detect_icon(name, st.st_mode)} {txt}"
        if colors:
            txt = colorize(txt, st.st_mode)

        print(prefix + connector + txt)

        if stat.S_ISDIR(st.st_mode):
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(path, new_prefix, icons, colors)


# ------------------------------------------------------------
# Recursive normal listing (-R)
# ------------------------------------------------------------


def list_recursive(base: str, args, depth=0) -> None:
    if depth > 0:
        print(f"\n{base}:")
    try:
        names = os.listdir(base)
    except PermissionError:
        print("Permission denied:", base)
        return

    names = sorted(names)
    gitmap = get_git_status_for_dir(base) if args.git else {}
    entries = []

    for n in names:
        if not args.all and n.startswith("."):
            continue
        path = os.path.join(base, n)
        try:
            st = os.lstat(path)
        except FileNotFoundError:
            continue

        link_t = None
        if stat.S_ISLNK(st.st_mode):
            try:
                link_t = os.readlink(path)
            except OSError:
                link_t = None

        git = gitmap.get(n)
        entries.append(Entry(path, n, st, link_t, git))

    print_entries(entries, args)

    for e in entries:
        if stat.S_ISDIR(e.stat.st_mode):
            list_recursive(e.path, args, depth + 1)


# ------------------------------------------------------------
# Output router
# ------------------------------------------------------------


def print_entries(entries: list[Entry], args) -> None:
    if args.json:
        out = []
        for e in entries:
            out.append(
                {
                    "name": e.name,
                    "size": e.stat.st_size,
                    "mode": mode_to_string(e.stat.st_mode),
                    "mtime": e.stat.st_mtime,
                    "git": e.git,
                    "type": (
                        "dir" if stat.S_ISDIR(e.stat.st_mode) else ("link" if stat.S_ISLNK(e.stat.st_mode) else "file")
                    ),
                }
            )
        print(json.dumps(out, indent=2))
        return

    if args.long:
        output_long(
            entries,
            icons=args.icons,
            colors=not args.no_color,
        )
        return

    # 2-column default
    output_columns(
        entries,
        icons=args.icons,
        colors=not args.no_color,
    )


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Files or directories",
    )
    p.add_argument("-l", "--long", action="store_true")
    p.add_argument("-a", "--all", action="store_true")
    p.add_argument("-R", "--recursive", action="store_true")
    p.add_argument("--tree", action="store_true")
    p.add_argument("--icons", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("--git", action="store_true")
    p.add_argument("--no-color", action="store_true")
    args = p.parse_args()

    for path in args.paths:
        if len(args.paths) > 1:
            print(f"{path}:")
        if args.tree:
            print_tree(
                path,
                icons=args.icons,
                colors=not args.no_color,
            )
            continue
        if args.recursive:
            list_recursive(path, args)
            continue

        if os.path.isfile(path) or os.path.islink(path):
            try:
                st = os.lstat(path)
            except FileNotFoundError:
                continue
            git = None
            if args.git:
                gitmap = get_git_status_for_dir(os.path.dirname(path))
                git = gitmap.get(os.path.basename(path))
            e = Entry(
                os.path.dirname(path),
                os.path.basename(path),
                st,
                git=git,
            )
            print_entries([e], args)
            continue

        # Directory
        try:
            names = os.listdir(path)
        except PermissionError:
            print("Permission denied:", path)
            continue
        names = sorted(names)

        gitmap = get_git_status_for_dir(path) if args.git else {}
        entries = []
        for n in names:
            if not args.all and n.startswith("."):
                continue
            fp = os.path.join(path, n)
            try:
                st = os.lstat(fp)
            except FileNotFoundError:
                continue
            link_t = None
            if stat.S_ISLNK(st.st_mode):
                try:
                    link_t = os.readlink(fp)
                except OSError:
                    link_t = None
            entries.append(
                Entry(
                    fp,
                    n,
                    st,
                    link_t,
                    gitmap.get(n),
                )
            )

        print_entries(entries, args)


if __name__ == "__main__":
    main()
