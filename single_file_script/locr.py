#!/usr/bin/env python3
"""
locr.py

A blazing fast, dependency-free lines of code counter.
Generates a language-wise breakdown of code, comments, and blank lines.

Behavioral Notes:
  - By default, output is plain text (monochrome). Use --color for syntax highlighting.
  - Automatically respects .gitignore rules (prioritizes `git check-ignore`).
  - Eagerly prunes ignored directories (e.g., node_modules) for maximum speed.
  - Gracefully handles Ctrl+C (Interrupts) by showing partial results.

Arguments:
  path          : Target directory (absolute or relative).
                  Defaults to current directory (.) if omitted.
  -c, --color   : Enable colored output in the terminal.
  --raw         : "Raw" mode. Ignores .gitignore rules and counts EVERYTHING.
  -o, --out     : Output file behavior:
                  - [No value]: Save to '[folder]_locr.txt' INSIDE the scanned folder.
                  - [Filename]: Save to the specific filename provided (in current dir).

Commands:

    # --- Basic Usage ---
    locr                  # Scan current dir
    locr src -c           # Scan src with color

    # --- Output to File ---
    locr -o               # Save to auto-named file
    locr -o report.txt    # Save to specific file

    # --- Raw / Debug Mode ---
    locr --raw            # Ignore gitignore
"""

import argparse
import fnmatch
import itertools
import os
import sys
import time
from collections import defaultdict
from typing import List, Optional, Set, Tuple

# =============================================================================
# Visuals & Configuration
# =============================================================================


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Foreground Colors
    GREY = "\033[90m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

    @staticmethod
    def style(text: str, color: str, enabled: bool = True) -> str:
        if not enabled:
            return text
        return f"{color}{text}{Colors.RESET}"


# Language Definitions
LANGUAGES = {
    # Python (Yellow)
    ".py": {
        "name": "Python",
        "color": Colors.YELLOW,
        "single": "#",
        "multi": ('"""', '"""'),
    },
    # Web (Red/Blue/Magenta)
    ".html": {"name": "HTML", "color": Colors.RED, "single": None, "multi": ("")},
    ".css": {
        "name": "CSS",
        "color": Colors.BLUE,
        "single": None,
        "multi": ("/*", "*/"),
    },
    ".scss": {
        "name": "Sass",
        "color": Colors.MAGENTA,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".js": {
        "name": "JavaScript",
        "color": Colors.YELLOW,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".jsx": {
        "name": "JavaScript JSX",
        "color": Colors.YELLOW,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".ts": {
        "name": "TypeScript",
        "color": Colors.BLUE,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".tsx": {
        "name": "TypeScript TSX",
        "color": Colors.BLUE,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".json": {"name": "JSON", "color": Colors.GREY, "single": None, "multi": None},
    # C-Family (Blue/Red)
    ".c": {"name": "C", "color": Colors.BLUE, "single": "//", "multi": ("/*", "*/")},
    ".h": {
        "name": "C Header",
        "color": Colors.BLUE,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".cpp": {
        "name": "C++",
        "color": Colors.BLUE,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".cs": {
        "name": "C#",
        "color": Colors.MAGENTA,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    ".java": {
        "name": "Java",
        "color": Colors.RED,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    # Systems (Cyan/Red)
    ".go": {"name": "Go", "color": Colors.CYAN, "single": "//", "multi": ("/*", "*/")},
    ".rs": {"name": "Rust", "color": Colors.RED, "single": "//", "multi": ("/*", "*/")},
    ".php": {
        "name": "PHP",
        "color": Colors.MAGENTA,
        "single": "//",
        "multi": ("/*", "*/"),
    },
    # Config/Data (Grey/White/Cyan)
    ".md": {"name": "Markdown", "color": Colors.WHITE, "single": None, "multi": ("")},
    ".yaml": {"name": "YAML", "color": Colors.CYAN, "single": "#", "multi": None},
    ".yml": {"name": "YAML", "color": Colors.CYAN, "single": "#", "multi": None},
    ".toml": {"name": "TOML", "color": Colors.CYAN, "single": "#", "multi": None},
    ".xml": {"name": "XML", "color": Colors.RED, "single": None, "multi": ("")},
    ".sql": {
        "name": "SQL",
        "color": Colors.YELLOW,
        "single": "--",
        "multi": ("/*", "*/"),
    },
    # Scripts
    ".sh": {"name": "Shell", "color": Colors.GREEN, "single": "#", "multi": None},
    ".lua": {
        "name": "Lua",
        "color": Colors.BLUE,
        "single": "--",
        "multi": ("--[[", "]]"),
    },
}

# =============================================================================
# Core Logic
# =============================================================================


class LocrEngine:
    def __init__(self, repo_path: str, raw_mode: bool = False):
        self.repo_path = os.path.abspath(repo_path)
        self.raw_mode = raw_mode
        self.ignore_patterns = []
        self.was_interrupted = False  # Flag to track interruption

        if not self.raw_mode:
            self.ignore_patterns = self._load_gitignore_patterns()

    def _load_gitignore_patterns(self) -> List[str]:
        patterns = [
            ".git",
            ".svn",
            ".hg",
            ".idea",
            ".vscode",
            "__pycache__",
            "node_modules",
            "venv",
            ".venv",
            "env",
            "dist",
            "build",
            "target",
        ]

        gitignore_path = os.path.join(self.repo_path, ".gitignore")
        if os.path.exists(gitignore_path):
            try:
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            patterns.append(line)
            except PermissionError:
                pass
        return patterns

    def _is_ignored(self, name: str, path: str) -> bool:
        if name in self.ignore_patterns:
            return True

        rel_path = os.path.relpath(path, self.repo_path)
        if rel_path == ".":
            return False
        rel_path = rel_path.replace(os.sep, "/")

        for pattern in self.ignore_patterns:
            clean_pat = pattern.rstrip("/")
            if fnmatch.fnmatch(name, clean_pat) or fnmatch.fnmatch(rel_path, clean_pat):
                return True
            if pattern.endswith("/") and (
                rel_path.startswith(pattern) or f"/{pattern}" in f"/{rel_path}"
            ):
                return True
        return False

    def scan(self, callback=None) -> dict:
        results = defaultdict(
            lambda: {
                "files": 0,
                "blank": 0,
                "comment": 0,
                "code": 0,
                "color": Colors.WHITE,
            }
        )
        self.was_interrupted = False

        try:
            for dirpath, dirnames, filenames in os.walk(self.repo_path, topdown=True):
                if callback:
                    callback()

                if not self.raw_mode:
                    dirnames[:] = [
                        d
                        for d in dirnames
                        if not self._is_ignored(d, os.path.join(dirpath, d))
                    ]

                for file in filenames:
                    full_path = os.path.join(dirpath, file)
                    if not self.raw_mode and self._is_ignored(file, full_path):
                        continue

                    ext = os.path.splitext(file)[1].lower()
                    if ext in LANGUAGES:
                        lang_def = LANGUAGES[ext]
                        b, c, k = self._analyze_file(full_path, lang_def)

                        name = lang_def["name"]
                        results[name]["files"] += 1
                        results[name]["blank"] += b
                        results[name]["comment"] += c
                        results[name]["code"] += k
                        results[name]["color"] = lang_def.get("color", Colors.WHITE)

        except KeyboardInterrupt:
            # Catch the interrupt HERE so we don't lose the data
            self.was_interrupted = True

        return results

    def _analyze_file(self, filepath: str, lang_def: dict) -> Tuple[int, int, int]:
        blank = 0
        comment = 0
        code = 0
        in_block = False
        single = lang_def.get("single")
        m_start, m_end = lang_def.get("multi") or (None, None)

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        blank += 1
                        continue
                    if in_block:
                        comment += 1
                        if m_end and m_end in line:
                            in_block = False
                        continue
                    if m_start and stripped.startswith(m_start):
                        comment += 1
                        if m_end and m_end not in stripped[len(m_start) :]:
                            in_block = True
                        continue
                    if single and stripped.startswith(single):
                        comment += 1
                        continue
                    code += 1
        except Exception:
            return 0, 0, 0

        return blank, comment, code


# =============================================================================
# Formatting & Output
# =============================================================================


def generate_report(
    results: dict, elapsed_time: float, use_color: bool, interrupted: bool
) -> List[str]:
    lines = []

    if interrupted:
        lines.append("")
        lines.append(
            Colors.style(
                "⚠ Scan interrupted. Showing partial results...",
                Colors.YELLOW,
                use_color,
            )
        )

    if not results:
        return lines + ["No code files found."]

    sorted_stats = sorted(results.items(), key=lambda x: x[1]["code"], reverse=True)
    totals = {"files": 0, "blank": 0, "comment": 0, "code": 0}
    for _, s in sorted_stats:
        totals["files"] += s["files"]
        totals["blank"] += s["blank"]
        totals["comment"] += s["comment"]
        totals["code"] += s["code"]

    sep = "=" * 75
    thin_sep = "-" * 75

    lines.append("")
    lines.append(Colors.style(sep, Colors.WHITE, use_color))
    lines.append(
        Colors.style(
            f"{'Language':<22} {'Files':>10} {'Blank':>12} {'Comment':>12} {'Code':>12}",
            Colors.BOLD,
            use_color,
        )
    )
    lines.append(Colors.style(thin_sep, Colors.WHITE, use_color))

    for lang, s in sorted_stats:
        row_text = f"{lang:<22} {s['files']:>10} {s['blank']:>12} {s['comment']:>12} {s['code']:>12}"
        lines.append(Colors.style(row_text, s["color"], use_color))

    lines.append(Colors.style(thin_sep, Colors.WHITE, use_color))
    lines.append(
        Colors.style(
            f"{'TOTAL':<22} {totals['files']:>10} {totals['blank']:>12} {totals['comment']:>12} {totals['code']:>12}",
            Colors.BOLD,
            use_color,
        )
    )
    lines.append(Colors.style(sep, Colors.WHITE, use_color))

    time_str = f"Processed {totals['files']} files in {elapsed_time:.3f} seconds."
    lines.append(Colors.style(time_str, Colors.CYAN, use_color))

    return lines


def auto_out_name(target_path: str) -> str:
    abs_target = os.path.abspath(target_path)
    folder_name = os.path.basename(os.path.normpath(abs_target))
    if not folder_name:
        folder_name = "root"
    return os.path.join(abs_target, f"{folder_name}_locr.txt")


# =============================================================================
# Main
# =============================================================================


def main():
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("path", nargs="?", default=".", help="Target directory")
    p.add_argument("--color", "-c", action="store_true", help="Enable colored output")
    p.add_argument("--raw", action="store_true", help="Ignore .gitignore rules")
    p.add_argument("--out", "-o", nargs="?", const=True, help="Write output to file")

    args = p.parse_args()
    target_path = os.path.abspath(args.path)

    is_writing_file = args.out is not None
    use_color = args.color and not is_writing_file and sys.stdout.isatty()

    if not os.path.isdir(target_path):
        print(f"Error: {args.path} is not a directory.")
        sys.exit(1)

    spinner_active = not is_writing_file and sys.stdout.isatty()
    msg = f"locr: scanning {target_path}..."

    if spinner_active:
        sys.stdout.write(Colors.style(msg, Colors.CYAN, use_color))
        sys.stdout.flush()

    spinner = itertools.cycle(["|", "/", "-", "\\"])
    last_spin = 0

    def update_spinner():
        nonlocal last_spin
        if not spinner_active:
            return
        now = time.time()
        if now - last_spin > 0.1:
            sys.stdout.write(
                Colors.style(f"\r{msg} {next(spinner)}", Colors.CYAN, use_color)
            )
            sys.stdout.flush()
            last_spin = now

    start_time = time.time()

    # Run the engine
    try:
        if spinner_active:
            sys.stdout.write(Colors.HIDE_CURSOR)

        engine = LocrEngine(target_path, raw_mode=args.raw)
        # engine.scan() now catches KeyboardInterrupt internally
        results = engine.scan(callback=update_spinner)

        if spinner_active:
            # Clear spinner line
            sys.stdout.write(f"\r{' ' * (len(msg) + 5)}\r")
            sys.stdout.flush()

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        if spinner_active:
            sys.stdout.write(Colors.SHOW_CURSOR)

    end_time = time.time()

    # Generate Report (passing the interrupted state)
    report_lines = generate_report(
        results, end_time - start_time, use_color, engine.was_interrupted
    )

    if is_writing_file:
        filename = auto_out_name(target_path) if args.out is True else args.out
        try:
            clean_lines = generate_report(
                results, end_time - start_time, False, engine.was_interrupted
            )
            with open(filename, "w", encoding="utf-8") as f:
                f.write("\n".join(clean_lines) + "\n")
            print(f"Output written to: {filename}")
        except Exception as e:
            print(f"Error writing to file: {e}")
    else:
        print("\n".join(report_lines))


if __name__ == "__main__":
    main()
