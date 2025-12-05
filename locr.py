#!/usr/bin/env python3
"""
locr.py

A blazing fast, dependency-free lines of code counter.
Generates a language-wise breakdown of code, comments, and blank lines.

Behavioral Notes:
  - Uses a "Hybrid" engine: Prunes heavy folders eagerly, then uses Git for 100% accuracy.
  - Automatically respects .gitignore rules (prioritizes `git check-ignore`).
  - Eagerly prunes ignored directories (e.g., node_modules) for maximum speed.
  - Ignores binary files and .git folder contents automatically.

Arguments:
  path          : Target directory (absolute or relative).
                  Defaults to current directory (.) if omitted.
  -c, --color   : Enable colored output in the terminal.
  -s, --stats   : Show percentage statistics (Share % and Density %).
  --raw         : "Raw" mode. Ignores .gitignore rules and counts EVERYTHING.
  -o, --out     : Output file behavior:
                  - [No value]: Save to '[folder]_locr.txt' INSIDE the scanned folder.
                  - [Filename]: Save to the specific filename provided (in current dir).

Commands:

    # --- Basic Usage (Clean View) ---
    # Scan current directory
    locr
    python locr.py

    # Scan a specific folder
    locr src
    python locr.py src

    # Scan a specific folder with Color
    locr src --color
    python locr.py src -c

    # --- Detailed Statistics (With %) ---
    # Show percentages for file share and comment density
    locr --stats
    locr -s

    # Combine with specific targets
    locr src -s
    python locr.py src --stats

    # --- Output to File ---
    # Save clean report to 'src_locr.txt'
    locr src -o
    
    # Save DETAILED stats to a file
    locr src -s -o stats_report.txt

    # --- Raw / Debug Mode ---
    # Scan everything (including ignored files) with stats
    locr --raw -s
    python locr.py --raw --stats
"""

import argparse
import fnmatch
import itertools
import os
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from typing import List, Tuple, Set, Optional

# --- IMPORT CONFIG ---
try:
    from locr_config import DEFAULT_IGNORE_PATTERNS, LANGUAGES, Colors
except ImportError:
    print("Error: locr_config.py not found. Please ensure it is in the same directory.")
    sys.exit(1)

# =============================================================================
# Core Logic
# =============================================================================


class LocrEngine:
    def __init__(self, repo_path: str, raw_mode: bool = False):
        self.repo_path = os.path.abspath(repo_path)
        self.raw_mode = raw_mode
        self.was_interrupted = False
        
        # Load default patterns for "Eager Pruning" (fast skip)
        self.simple_patterns = []
        if not self.raw_mode:
            self.simple_patterns = self._load_default_patterns()

    def _load_default_patterns(self) -> List[Tuple[str, bool, bool]]:
        # Load defaults + root .gitignore for the "fast prune" phase
        patterns = DEFAULT_IGNORE_PATTERNS[:]
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
        
        # Compile them for fnmatch
        compiled = []
        for raw in patterns:
            p = raw.strip()
            is_dir = p.endswith("/")
            if is_dir: p = p[:-1]
            anchored = p.startswith("/")
            if anchored: p = p[1:]
            p = p.replace("\\", "/")
            compiled.append((p, is_dir, anchored))
        return compiled

    def _simple_gitignore_match(self, relpath: str, patterns: List[Tuple[str, bool, bool]]) -> bool:
        if not patterns: return False
        for pat, is_dir, anchored in patterns:
            if anchored:
                if fnmatch.fnmatch(relpath, pat) or fnmatch.fnmatch(relpath, pat + "/"):
                    return (relpath == pat or relpath.startswith(pat + "/")) if is_dir else True
            elif fnmatch.fnmatch(relpath, pat) or fnmatch.fnmatch(os.path.basename(relpath), pat):
                return (relpath == pat or relpath.startswith(pat + "/")) if is_dir else True
        return False

    def _is_git_repo(self) -> bool:
        return os.path.isdir(os.path.join(self.repo_path, ".git"))

    def _git_check_ignore(self, relpaths: List[str]) -> Set[str]:
        if not relpaths: return set()
        try:
            # Batch query Git for accuracy
            input_bytes = "\0".join(relpaths).encode("utf-8")
            proc = subprocess.run(
                ["git", "check-ignore", "--stdin", "-z"],
                input=input_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                cwd=self.repo_path,
                timeout=15, # Generous timeout for large repos
            )
            if proc.returncode not in (0, 1) or not proc.stdout:
                return set()
            parts = [p.decode("utf-8") for p in proc.stdout.split(b"\0") if p]
            return set(parts)
        except Exception:
            return set()

    def _collect_and_filter_files(self, callback=None) -> List[str]:
        """
        Phase 1: Collect all files, but eager-prune junk folders.
        Phase 2: Use Git to filter the survivors.
        """
        all_rel_paths = []
        
        # --- PHASE 1: WALK & PRUNE ---
        try:
            for dirpath, dirnames, filenames in os.walk(self.repo_path, topdown=True):
                if callback: callback()
                
                rel_dir = os.path.relpath(dirpath, self.repo_path)
                if rel_dir == ".": rel_dir = ""
                else: rel_dir = rel_dir.replace(os.sep, "/")

                if not self.raw_mode:
                    # Eager Pruning: Remove directories that match simple patterns
                    # This prevents us from walking into node_modules or .git
                    active_dirs = []
                    for d in dirnames:
                        if d == ".git": continue
                        path_to_check = (rel_dir + "/" + d) if rel_dir else d
                        if not self._simple_gitignore_match(path_to_check, self.simple_patterns):
                            active_dirs.append(d)
                    dirnames[:] = active_dirs

                for f in filenames:
                    # Basic extension check (optimization: don't track binary files)
                    ext = os.path.splitext(f)[1].lower()
                    if ext not in LANGUAGES:
                        continue
                        
                    rel_path = (rel_dir + "/" + f if rel_dir else f).replace(os.sep, "/")
                    
                    if not self.raw_mode and self._simple_gitignore_match(rel_path, self.simple_patterns):
                        continue
                        
                    all_rel_paths.append(rel_path)

        except KeyboardInterrupt:
            self.was_interrupted = True
            return []

        if self.raw_mode or not all_rel_paths:
            return all_rel_paths

        # --- PHASE 2: GIT ACCURACY ---
        final_list = []
        ignored_by_git = set()
        
        if self._is_git_repo():
            ignored_by_git = self._git_check_ignore(all_rel_paths)
            
        for p in all_rel_paths:
            if p not in ignored_by_git:
                final_list.append(p)
                
        return final_list

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
            # Step 1: Get the clean list of files (Pruned + Git Verified)
            valid_files = self._collect_and_filter_files(callback)

            # Step 2: Analyze them
            for rel_path in valid_files:
                if self.was_interrupted: break
                if callback: callback()

                full_path = os.path.join(self.repo_path, rel_path)
                ext = os.path.splitext(rel_path)[1].lower()
                
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
    results: dict, elapsed_time: float, use_color: bool, interrupted: bool, show_stats: bool
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

    # 1. Pre-calculate Totals
    total_files = 0
    total_blank = 0
    total_comment = 0
    total_code = 0
    
    for s in results.values():
        total_files += s["files"]
        total_blank += s["blank"]
        total_comment += s["comment"]
        total_code += s["code"]
        
    grand_total_lines = total_blank + total_comment + total_code
    safe_total_files = total_files if total_files > 0 else 1

    sorted_stats = sorted(results.items(), key=lambda x: x[1]["code"], reverse=True)

    # 2. Determine Widths based on Content (Not Terminal)
    if show_stats:
        # Stats View: 20 + 1 + 12 + 1 + 14 + 1 + 14 + 1 + 14 = 78 chars
        content_width = 78
        header_fmt = "{:<20} {:>12} {:>14} {:>14} {:>14}"
        row_fmt    = "{:<20} {:>12} {:>14} {:>14} {:>14}"
    else:
        # Clean View: 22 + 1 + 10 + 1 + 12 + 1 + 12 + 1 + 12 = 72 chars
        content_width = 72
        header_fmt = "{:<22} {:>10} {:>12} {:>12} {:>12}"
    
    sep = "=" * content_width
    thin_sep = "-" * content_width

    lines.append("")
    lines.append(Colors.style(sep, Colors.WHITE, use_color))

    # 3. Build Table
    if show_stats:
        # === DETAILED VIEW (WITH %) ===
        lines.append(Colors.style(header_fmt.format("Language", "Files", "Blank", "Comment", "Code"), Colors.BOLD, use_color))
        lines.append(Colors.style(thin_sep, Colors.WHITE, use_color))

        for lang, s in sorted_stats:
            l_lines = s["blank"] + s["comment"] + s["code"]
            safe_lines = l_lines if l_lines > 0 else 1
            
            f_pct = (s["files"] / safe_total_files) * 100
            b_pct = (s["blank"] / safe_lines) * 100
            c_pct = (s["comment"] / safe_lines) * 100
            k_pct = (s["code"] / safe_lines) * 100
            
            lines.append(Colors.style(row_fmt.format(
                lang, 
                f"{s['files']} ({f_pct:.0f}%)", 
                f"{s['blank']} ({b_pct:.0f}%)", 
                f"{s['comment']} ({c_pct:.0f}%)", 
                f"{s['code']} ({k_pct:.0f}%)"
            ), s["color"], use_color))
            
        # Global Totals
        safe_global = grand_total_lines if grand_total_lines > 0 else 1
        gt_b_pct = (total_blank / safe_global) * 100
        gt_c_pct = (total_comment / safe_global) * 100
        gt_k_pct = (total_code / safe_global) * 100
        
        lines.append(Colors.style(thin_sep, Colors.WHITE, use_color))
        lines.append(Colors.style(row_fmt.format(
            "TOTAL", 
            f"{total_files} (100%)", 
            f"{total_blank} ({gt_b_pct:.0f}%)", 
            f"{total_comment} ({gt_c_pct:.0f}%)", 
            f"{total_code} ({gt_k_pct:.0f}%)"
        ), Colors.BOLD, use_color))

    else:
        # === SIMPLE VIEW (NO %) ===
        lines.append(Colors.style(header_fmt.format("Language", "Files", "Blank", "Comment", "Code"), Colors.BOLD, use_color))
        lines.append(Colors.style(thin_sep, Colors.WHITE, use_color))

        for lang, s in sorted_stats:
            lines.append(Colors.style(header_fmt.format(
                lang, s['files'], s['blank'], s['comment'], s['code']
            ), s["color"], use_color))

        lines.append(Colors.style(thin_sep, Colors.WHITE, use_color))
        lines.append(Colors.style(header_fmt.format(
            "TOTAL", total_files, total_blank, total_comment, total_code
        ), Colors.BOLD, use_color))

    # --- FOOTER ---
    lines.append(Colors.style(sep, Colors.WHITE, use_color))
    time_str = f"Processed {total_files} files in {elapsed_time:.3f} seconds."
    lines.append(Colors.style(time_str, Colors.CYAN, use_color))
    lines.append("")

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
    p.add_argument("--stats", "-s", action="store_true", help="Show percentage statistics")

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

    if spinner_active:
        sys.stdout.write(Colors.HIDE_CURSOR)

    try:
        engine = LocrEngine(target_path, raw_mode=args.raw)
        results = engine.scan(callback=update_spinner)
        
        if spinner_active:
            w = shutil.get_terminal_size().columns
            sys.stdout.write(f"\r{' ' * (w - 1)}\r")
            sys.stdout.flush()

    except Exception as e:
        if spinner_active:
            w = shutil.get_terminal_size().columns
            sys.stdout.write(f"\r{' ' * (w - 1)}\r")
            sys.stdout.flush()
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        if spinner_active:
            sys.stdout.write(Colors.SHOW_CURSOR)

    end_time = time.time()

    report_lines = generate_report(
        results, 
        end_time - start_time, 
        use_color, 
        engine.was_interrupted,
        show_stats=args.stats
)

    if is_writing_file:
        filename = auto_out_name(target_path) if args.out is True else args.out
        try:
            clean_lines = generate_report(
                results, 
                end_time - start_time, 
                False, 
                engine.was_interrupted,
                show_stats=args.stats
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