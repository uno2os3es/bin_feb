#!/data/data/com.termux/files/usr/bin/env python3
"""Offline requirements.txt generator (full rewrite).

Features:
- archive support (.zip/.whl/.tar.gz/.tgz/.tar.xz)
- notebooks (.ipynb)
- shebang (no extension python scripts)
- ignore paths
- tqdm progress bar
- import -> package mapping file support
- stdlib exclusion
- offline pip.txt verification
- multiprocessing
- persistent caching of file analysis
- exclude local/project imports (relative and modules present in repo)
- fully resolve namespace packages (top-level) with mapping fallback
- trace `from module import *` by examining module sources for __all__ and internal imports
- static detection of dynamic imports (importlib.import_module, __import__)
"""

from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import json
import multiprocessing as mp
import os
import sys
import tarfile
import zipfile
from pathlib import Path

import regex as re
from dh import PKG_MAPPING, STDLIB
from tqdm import tqdm

# Default cache file (in project dir)
CACHE_FILE = ".reqcache.json"

# ----------------------------- Utilities -----------------------------------


def fast_hash(path: Path) -> str:
    """Efficient hash: hash first 4KB + size + mtime to be quick."""
    try:
        h = hashlib.sha256()
        stat = path.stat()
        h.update(str(stat.st_size).encode())
        h.update(str(int(stat.st_mtime)).encode())
        with open(path, "rb") as f:
            h.update(f.read(4096))
        return h.hexdigest()
    except Exception:
        return "0"


def load_json(path: Path) -> dict:
    try:
        with open(
                path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            return json.load(f)
    except Exception:
        return {}


def save_json(path: Path, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


# ------------------------ Support files loading ----------------------------


def load_set_file(path: str) -> set[str]:
    out = set()
    try:
        with open(
                path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            for line in f:
                v = line.strip()
                if v:
                    out.add(v)
    except Exception:
        pass
    return out


def load_mapping(path: str) -> dict[str, str]:
    """Mapping file: lines like `module=subpackage-package` or `pkg.submod=package-name`."""
    out: dict[str, str] = {}
    try:
        with open(
                path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip()
    except Exception:
        pass
    return out


# ------------------------- AST EXTRACTION HELPERS --------------------------


def extract_from_ast(code: str,
                     path_hint: str | None = None) -> dict[str, set[str]]:
    """Parse Python source and extract:
      - imports: top-level names imported (first component)
      - star_imports: modules used in `from X import *`
      - dynamic_imports: string literals used in importlib.import_module/__import__
      - relative_imports: modules imported with level > 0 (local)
    Returns a dict of sets.
    """
    result = {
        "imports": set(),  # e.g., "requests", "os"
        "star_modules": set(),  # modules used in from X import *
        "dynamic": set(),  # string-literal dynamic imports detected
        "relative": set(),  # local relative imports (module names or ".")
    }

    try:
        tree = ast.parse(code)
    except Exception:
        # fallback: simple regexes for dynamic import strings
        for m in re.finditer(
                r"(?:import_module|__import__)\(\s*['\"]([\w\.]+)['\"]\s*\)",
                code,
        ):
            result["dynamic"].add(m.group(1).split(".", 1)[0])
        return result

    for node in ast.walk(tree):
        # static imports
        if isinstance(node, ast.Import):
            for a in node.names:
                first = a.name.split(".", 1)[0]
                result["imports"].add(first)

        elif isinstance(node, ast.ImportFrom):
            # relative import detection
            if node.level and node.level > 0:
                # mark as local/relative
                if node.module:
                    result["relative"].add(node.module.split(".", 1)[0])
                else:
                    result["relative"].add(".")
                continue

            if node.module:
                base = node.module.split(".", 1)[0]
                if any(name.name == "*" for name in node.names):
                    result["star_modules"].add(node.module)
                else:
                    result["imports"].add(base)

        # dynamic import detection (__import__('pkg') or importlib.import_module('pkg'))
        elif isinstance(node, ast.Call):
            # __import__('pkg')
            if isinstance(node.func,
                          ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0],
                                            ast.Constant) and isinstance(
                                                node.args[0].value, str):
                    result["dynamic"].add(node.args[0].value.split(".", 1)[0])
            # importlib.import_module('pkg')
            elif isinstance(node.func, ast.Attribute):
                val = node.func
                if (isinstance(val.value, ast.Name)
                        and val.value.id == "importlib" and val.attr
                        == "import_module") and (node.args and isinstance(
                            node.args[0],
                            ast.Constant,
                        ) and isinstance(
                            node.args[0].value,
                            str,
                        )):
                    result["dynamic"].add(node.args[0].value.split(".", 1)[0])

    # As a final pass, if star imports exist, try to also detect imports inside the module by scanning the file for 'from x import y' patterns (handled later when tracing star modules).
    return result


# --------------------------- FILE PROCESSORS --------------------------------


def process_py_file_content(code: str,
                            path_hint: str | None = None
                            ) -> dict[str, list[str]]:
    d = extract_from_ast(code, path_hint)
    return {k: sorted(v) for k, v in d.items()}


def process_py_file(path: Path, ) -> dict[str, list[str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return {
            "imports": [],
            "star_modules": [],
            "dynamic": [],
            "relative": [],
        }
    return process_py_file_content(text, str(path))


def process_noext_python_script(path: Path, ) -> dict[str, list[str]]:
    try:
        with open(
                path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            first = f.readline()
            if "#!" not in first or "python" not in first.lower():
                return {
                    "imports": [],
                    "star_modules": [],
                    "dynamic": [],
                    "relative": [],
                }
            code = f.read()
    except Exception:
        return {
            "imports": [],
            "star_modules": [],
            "dynamic": [],
            "relative": [],
        }
    return process_py_file_content(code, str(path))


def process_ipynb(path: Path, ) -> dict[str, list[str]]:
    out = {
        "imports": [],
        "star_modules": [],
        "dynamic": [],
        "relative": [],
    }
    try:
        with open(
                path,
                encoding="utf-8",
                errors="ignore",
        ) as f:
            nb = json.load(f)
    except Exception:
        return out
    imports = set()
    stars = set()
    dyn = set()
    rel = set()
    for cell in nb.get("cells", []):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", []))
            d = extract_from_ast(src, str(path))
            imports |= d["imports"]
            stars |= d["star_modules"]
            dyn |= d["dynamic"]
            rel |= d["relative"]
    out["imports"] = sorted(imports)
    out["star_modules"] = sorted(stars)
    out["dynamic"] = sorted(dyn)
    out["relative"] = sorted(rel)
    return out


def process_zip_file(path: Path, ) -> dict[str, list[str]]:
    imports = set()
    stars = set()
    dyn = set()
    rel = set()
    try:
        with zipfile.ZipFile(path, "r") as z:
            for name in z.namelist():
                if name.endswith(".py"):
                    try:
                        code = z.read(name).decode(
                            "utf-8",
                            errors="ignore",
                        )
                        d = extract_from_ast(code, f"{path}:{name}")
                        imports |= d["imports"]
                        stars |= d["star_modules"]
                        dyn |= d["dynamic"]
                        rel |= d["relative"]
                    except Exception:
                        pass
    except Exception:
        pass
    return {
        "imports": sorted(imports),
        "star_modules": sorted(stars),
        "dynamic": sorted(dyn),
        "relative": sorted(rel),
    }


def process_tar_file(path: Path, ) -> dict[str, list[str]]:
    imports = set()
    stars = set()
    dyn = set()
    rel = set()
    mode = "r:xz" if str(path).endswith(".xz") else "r:gz"
    try:
        with tarfile.open(path, mode) as t:
            for m in t.getmembers():
                if m.isfile() and m.name.endswith(".py"):
                    try:
                        f = t.extractfile(m)
                        if not f:
                            continue
                        code = f.read().decode(
                            "utf-8",
                            errors="ignore",
                        )
                        d = extract_from_ast(
                            code,
                            f"{path}:{m.name}",
                        )
                        imports |= d["imports"]
                        stars |= d["star_modules"]
                        dyn |= d["dynamic"]
                        rel |= d["relative"]
                    except Exception:
                        pass
    except Exception:
        pass
    return {
        "imports": sorted(imports),
        "star_modules": sorted(stars),
        "dynamic": sorted(dyn),
        "relative": sorted(rel),
    }


# --------------------------- DISPATCH WORKER --------------------------------


def process_raw(path: str, ) -> dict[str, list[str]]:
    """Worker entry point. Returns a serializable dict with sets converted to lists."""
    p = Path(path)
    name = str(p).lower()

    if p.suffix == ".py":
        return process_py_file(p)
    if p.suffix == ".ipynb":
        return process_ipynb(p)
    if p.suffix == "" and p.is_file():
        return process_noext_python_script(p)
    if name.endswith(".zip") or name.endswith(".whl"):
        return process_zip_file(p)
    if name.endswith(".tar.gz") or name.endswith(".tgz") or name.endswith(
            ".tar.xz"):
        return process_tar_file(p)
    # else nothing
    return {
        "imports": [],
        "star_modules": [],
        "dynamic": [],
        "relative": [],
    }


# --------------------------- PROJECT MODULE MAP -----------------------------


def build_project_module_map(sources: list[str], ) -> dict[str, list[str]]:
    """Build a mapping of module dotted names -> file paths discovered in sources.
    We attempt:
      - path/to/pkg/mod.py -> pkg.mod
      - path/to/pkg/__init__.py -> pkg
    We include nested dotted names as possible matches.
    """
    mapping: dict[str, list[str]] = {}
    for fp in sources:
        p = Path(fp)
        if not p.exists():
            continue
        if p.suffix != ".py":
            # archives and others are handled dynamically when tracing star imports (not added here)
            continue
        # derive dotted path from relative path
        rel = os.path.normpath(fp).lstrip("./")
        parts = rel.split(os.sep)
        if parts[-1] == "__init__.py":
            mod = ".".join(parts[:-1]) if parts[:-1] else (
                parts[-2] if len(parts) > 1 else "")
        else:
            mod = ".".join(parts)[:-3] if rel.endswith(".py") else ".".join(
                parts)
        if not mod:
            continue
        # also register top-level first component
        top = mod.split(".", 1)[0]
        mapping.setdefault(mod, []).append(fp)
        mapping.setdefault(top, [*mapping.get(top, []), fp])
    return mapping


# ---------------------- STAR IMPORT / MODULE TRACING ------------------------


def trace_star_module(module: str, project_map: dict[str,
                                                     list[str]]) -> set[str]:
    """Given a module dotted path (e.g., "mypkg.submod"), attempt to find its source inside
    the project map and extract imports and any names listed in __all__.
    Returns a set of imported top-level names discovered inside that module.
    """
    found_imports = set()
    # try to find exact or package-level file path
    candidates = []
    if module in project_map:
        candidates += project_map[module]
    # try top-level module
    top = module.split(".", 1)[0]
    if top in project_map:
        candidates += project_map[top]
    # dedupe
    candidates = list(dict.fromkeys(candidates))

    for fp in candidates:
        try:
            text = Path(fp).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        d = extract_from_ast(text, fp)
        found_imports |= d["imports"]
        found_imports |= {m.split(".", 1)[0] for m in d["dynamic"]}
        # try to parse __all__
        try:
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target,
                                      ast.Name) and target.id == "__all__":
                            # evaluate if it's a simple list/tuple of literals
                            val = node.value
                            names = []
                            if isinstance(
                                    val,
                                (
                                    ast.List,
                                    ast.Tuple,
                                ),
                            ):
                                for elt in val.elts:
                                    if isinstance(
                                            elt,
                                            ast.Constant,
                                    ) and isinstance(
                                            elt.value,
                                            str,
                                    ):
                                        names.append(elt.value)
                            # If __all__ references modules (strings), we may treat them as submodules -> add top-level
                            for nm in names:
                                if "." in nm:
                                    found_imports.add(nm.split(".", 1)[0])
                # also catch simple "from .sub import X as Y" inside module -> local import; already handled in extract_from_ast.
        except Exception:
            pass
    return found_imports


# --------------------------- RESOLUTION ------------------------------------


def resolve_packages(
    imports: set[str],
    stdlib: set[str],
    mapping: dict[str, str],
    pip_available: set[str],
    project_toplevels: set[str],
) -> set[str]:
    """Map import names -> package names which should be placed into requirements.txt.

    Rules:
    - Skip if in stdlib
    - Skip if in project_toplevels (local module present)
    - Apply mapping: exact match or submodule match
    - Normalize to top-level package (first component) when appropriate
    - Keep only packages that appear in pip_available (offline list), otherwise still include them (option)
    """
    out = set()
    for imp in imports:
        if not imp:
            continue
        if imp in stdlib:
            continue
        if imp in project_toplevels:
            # local project module - skip
            continue
        # mapping attempts
        if imp in mapping:
            out_name = mapping[imp]
        else:
            # try longest prefix mapping: e.g. "google.cloud.storage" -> mapping has "google.cloud" etc.
            parts = imp.split(".")
            mapped = None
            for i in range(len(parts), 0, -1):
                key = ".".join(parts[:i])
                if key in mapping:
                    mapped = mapping[key]
                    break
            if mapped:
                out_name = mapped
            else:
                # fallback to top-level package
                out_name = parts[0]
        # prefer the actual pip_available name if present (case-insensitive)
        if pip_available:
            low = {p.lower(): p for p in pip_available}
            candidate_low = out_name.lower()
            if candidate_low in low:
                out.add(low[candidate_low])
                continue
        out.add(out_name)
    return out


# ---------------------------- SCAN SOURCES ---------------------------------


def scan_sources(ignore_dirs: set[str], ) -> list[str]:
    out = []
    for root, dirs, files in os.walk("."):
        # prune ignored directories early
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        for f in files:
            fp = os.path.join(root, f)
            lower = f.lower()
            # include python sources, archives, notebooks, or no-extension scripts
            if (lower.endswith(".py") or lower.endswith(".ipynb")
                    or lower.endswith(".whl") or lower.endswith(".zip")
                    or lower.endswith(".tar.gz") or lower.endswith(".tgz")
                    or lower.endswith(".tar.xz") or Path(fp).suffix == ""):
                out.append(fp)
    return out


# ------------------------------- MAIN --------------------------------------


def main() -> None:
    p = argparse.ArgumentParser(
        description="Offline requirements.txt generator (static + heuristics)."
    )
    p.add_argument(
        "--ignore",
        nargs="*",
        default=[
            "venv",
            ".venv",
            ".git",
            ".ipynb_checkpoints",
        ],
        help="Directories to ignore during scan",
    )
    p.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable cache usage",
    )
    p.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear cache and exit",
    )
    p.add_argument(
        "--pipfile",
        default="/sdcard/pip.txt",
        help="Offline pip package list (one per line)",
    )
    p.add_argument(
        "--cache-file",
        default=CACHE_FILE,
        help="Cache file path",
    )
    p.add_argument(
        "--out",
        default="requirements.txt",
        help="Output requirements file",
    )
    p.add_argument(
        "--include-unknown",
        action="store_true",
        default=True,
        help=
        "Include packages not present in offline pip list (default: only include those in piplist)",
    )
    args = p.parse_args()

    ignore_dirs = set(args.ignore)

    # load support files
    # stdlib = load_set_file(args.stdlib)
    # mapping = load_mapping(args.mapping)
    stdlib = STDLIB
    mapping = PKG_MAPPING
    piplist = load_set_file(args.pipfile)

    # scanning
    sources = scan_sources(ignore_dirs)
    sources = sorted(set(sources))

    # quick project toplevel detection: gather first components of py files and package directories
    project_map = build_project_module_map(sources)
    set(project_map.keys())  # module names and top-level names
    # but project_map has many dotted mappings; let's reduce to top-level names actually present
    project_top_only = {k.split(".", 1)[0] for k in project_map}

    # cache handling
    cache_path = Path(args.cache_file)
    cache = {} if args.no_cache else (
        load_json(cache_path) if cache_path.exists() else {})
    if args.clear_cache:
        try:
            if cache_path.exists():
                cache_path.unlink()
            print("Cache cleared.")
        except Exception as e:
            print("Failed clearing cache:", e)
        return

    tasks = []
    cached_results = []
    # Pre-check cache: we key cache by normalized relative path
    for path in sources:
        pth = Path(path)
        key = os.path.normpath(path)
        needs = True
        if not args.no_cache and key in cache:
            entry = cache[key]
            try:
                mtime = pth.stat().st_mtime
            except Exception:
                mtime = None
            h = fast_hash(pth) if mtime is not None else "0"
            if entry.get("mtime") == mtime and entry.get("hash") == h:
                cached_results.append(
                    entry.get(
                        "result",
                        {
                            "imports": [],
                            "star_modules": [],
                            "dynamic": [],
                            "relative": [],
                        },
                    ))
                needs = False
        if needs:
            tasks.append(path)

    # multiprocessing work
    computed_results = []
    if tasks:
        with mp.Pool(mp.cpu_count()) as pool:
            for res in tqdm(
                    pool.imap_unordered(process_raw, tasks),
                    total=len(tasks),
                    desc="Processing",
            ):
                computed_results.append(res)

    # update cache for processed tasks
    if not args.no_cache:
        for path, res in zip(tasks, computed_results, strict=False):
            key = os.path.normpath(path)
            try:
                mtime = Path(path).stat().st_mtime
            except Exception:
                mtime = None
            h = fast_hash(Path(path)) if mtime is not None else "0"
            cache[key] = {
                "mtime": mtime,
                "hash": h,
                "result": res,
            }
        with contextlib.suppress(Exception):
            save_json(cache_path, cache)

    # aggregate
    all_imports: set[str] = set()
    all_star_modules: set[str] = set()
    all_dynamic: set[str] = set()
    all_relative: set[str] = set()

    for r in cached_results + computed_results:
        all_imports |= set(r.get("imports", []))
        all_star_modules |= set(r.get("star_modules", []))
        all_dynamic |= set(r.get("dynamic", []))
        all_relative |= set(r.get("relative", []))

    # trace star imports by inspecting project sources for module definitions
    # this will add imports discovered inside the star-imported modules
    traced_from_star = set()
    if all_star_modules:
        for mod in tqdm(
                sorted(all_star_modules),
                desc="Tracing star imports",
        ):
            traced_from_star |= trace_star_module(mod, project_map)

    # include dynamic imports (best-effort)
    # also try to map dynamic imports if they use dotted paths
    dynamic_tops = {d.split(".", 1)[0] for d in all_dynamic}

    # combine discovered imports
    discovered = set(all_imports) | traced_from_star | dynamic_tops

    # exclude relative/local imports found earlier
    # local relative imports are in all_relative (like ".utils") and project_top_only
    # exclude any discovered import that is known to be project-local
    final_candidates = set()
    for imp in discovered:
        if not imp:
            continue
        if imp in stdlib:
            continue
        if imp in project_top_only:
            # local project module -> skip
            continue
        if imp in all_relative:
            # relative import indicates a local module
            continue
        final_candidates.add(imp)

    # resolve packages using mapping + piplist
    pkgs = resolve_packages(
        final_candidates,
        stdlib,
        mapping,
        piplist,
        project_top_only,
    )

    # apply piplist filter: if not include_unknown, intersect with piplist (case-insensitive)
    if not args.include_unknown and piplist:
        lowpip = {p.lower() for p in piplist}
        pkgs = {p for p in pkgs if p.lower() in lowpip}

    # write requirements
    out_file = Path(args.out)
    try:
        with out_file.open("w", encoding="utf-8") as f:
            for pkg in sorted(pkgs, key=lambda s: s.lower()):
                f.write(pkg + "\n")
    except Exception as e:
        print("Failed writing requirements file:", e)
        sys.exit(2)

    # Print summary
    print("\nGenerated", out_file.name)
    print("────────────────────────────")
    if pkgs:
        for pkg in sorted(pkgs, key=lambda s: s.lower()):
            print(pkg)
    else:
        print("(empty)")


if __name__ == "__main__":
    main()
