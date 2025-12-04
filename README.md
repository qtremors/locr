# Lines of Code in Repo (`locr`)

**locr** is a fast, dependency-free utility designed to count lines of code in Git repositories.

> *"Python is slow. You can't write a fast file scanner in Python."*
>
> — **The Haters** (probably)

They aren't wrong; Python *is* slower than Rust or Go. But **locr** cheats. Instead of walking through 50,000 files in `node_modules` and then ignoring them (like some tools do), `locr` ignores them *before* it even enters the folder. The result? A Python script that feels like it's written in C (probably).

> ℹ️ **Note:** `locr` is a **heuristic** counter designed for speed and convenience in Python environments. It is currently in **v1.0** and is optimized for standard web and software projects.

## Features

- **Hybrid Git-Awareness:** Uses a smart 2-phase scanner. It **eagerly prunes** massive junk folders (like `node_modules`) for speed, then queries `git check-ignore` for the remaining files to ensure **100% accuracy** with your `.gitignore` rules (including complex negations).
- **Eager Pruning:** Instantly skips heavy directories (`node_modules`, `venv`, `.git`) before even asking Git about them. This keeps scans blazing fast even on massive monorepos.
- **Graceful Interrupts:** Caught in a massive scan? Hit `Ctrl+C` to stop immediately and view the **partial results** collected so far.
- **Smart Colors:** Language-specific row coloring (Python=Yellow, HTML=Red, TypeScript=Blue) for instant visual scanning.
- **Visual Feedback:** Includes a high-visibility loading spinner that respects terminal performance limits.
- **Contextual Output:** Supports saving reports directly into the scanned folder or to a custom path.
- **Zero Dependencies:** Written in pure Python (standard library only).

## Installation

### 1. Install Globally (Recommended)

This allows you to run the command `locr` from any terminal window.

```bash
# Clone or download this repo, then navigate to it
git clone https://github.com/qtremors/locr.git
cd locr

# Install in editable mode
pip install -e .
````

*The `-e` flag stands for "editable". It links the global command to your local file, so any changes you make to `locr.py` apply immediately.*

### 2\. Standalone Usage

If you don't want to install it, you can just run the script directly:

```bash
python locr.py [arguments]
```

## Comparisons

How does `locr` stack up against the alternatives?

| Tool | Language | Strategy | Best For... |
| :--- | :--- | :--- | :--- |
| **`locr`** | Python | **Eager Pruning.** Skips heavy folders *before* entering them. | **Convenience.** No installation required if you have Python. Perfect for quick checks. |
| **`cloc`** | Perl | **Scan & Filter.** Walks tree first, filters later. | **Legacy Support.** Supports huge list of obscure languages (COBOL, Fortran). |
| **`tokei`** | Rust | **Raw Power.** Compiled binary speed. | **Performance.** The gold standard for speed, if you have the Rust toolchain. |
| **`scc`** | Go | **Complexity Analysis.** Fast parallel processing. | **Deep Stats.** If you need cyclomatic complexity scores. |

**The Bottom Line:** If you already have Rust or Go tools installed, keep using them—they are technically faster. But if you just want a tool that works *now* with the Python environment you already have, `locr` is the move.

## Usage & Commands

### Arguments Reference

| Argument | Short | Description |
|---|---|---|
| `path` | | **Target Directory.** Defaults to current directory (`.`) if omitted. |
| `--color` | `-c` | **Enable Color.** Turn on language-specific syntax highlighting. |
| `--out` | `-o` | **Save to file.** <br>1. **No Value:** Save to `[folder]_locr.txt` INSIDE the scanned folder.<br>2. **Filename:** Save to a specific file in the current directory. |
| `--raw` | | **Raw Mode.** Ignore `.gitignore` rules and count EVERYTHING. |

### Common Scenarios

#### 1\. Standard Scan (Plain Text)

Scans the current directory. Output is monochrome by default (safer for piping to files).

```bash
locr
```

**Expected Output:**

```
===========================================================================
Language                    Files        Blank      Comment         Code
---------------------------------------------------------------------------
JSON                            5            4            0         4717
TypeScript TSX                 21          257           19         2256
Python                         11           86           40          623
TypeScript                      7           36           14          239
Markdown                        1           91            0           99
CSS                             2           15            7           99
JavaScript                      3            1            1           48
HTML                            1            0            0           13
TOML                            1            0            0           11
---------------------------------------------------------------------------
TOTAL                          52          490           81         8105
===========================================================================
Processed 52 files in 0.032 seconds.
```

#### 2\. Colored Scan

Scans a specific folder (`src`) with syntax highlighting enabled.

```bash
locr src --color
```

#### 3\. Save to File (Auto-Location)

Scans the `frontend` folder and saves the report *inside* that folder.

```bash
locr frontend -o
```

**Console Output:**

```
Output written to: Z:\Projects\MyApp\frontend\frontend_locr.txt
```

#### 4\. Raw Mode (Debug)

Ignores your `.gitignore` and counts everything (virtual environments, build artifacts, etc).

```bash
locr --raw
```

#### 5\. Interrupting a Scan

If you start scanning a massive monorepo and realize you have enough data, press `Ctrl+C`.

```bash
locr giant-repo
# User presses Ctrl+C...
```

**Console Output:**

```
⚠ Scan interrupted. Showing partial results...

===========================================================================
Language                    Files        Blank      Comment         Code
---------------------------------------------------------------------------
Python                        458         6160         7293        30962
JavaScript                     88         4680         3970        19377
CSS                            16          955          114         4145
HTML                           63          221            0         1686
YAML                           17           83           10          938
Markdown                        6           30            0          113
TOML                            1            8            0           60
JSON                            1            0            0           19
---------------------------------------------------------------------------
TOTAL                         650        12137        11387        57300
===========================================================================
Processed 650 files in 0.422 seconds.
```

## Commands Cheat Sheet

Quick reference for common commands.

```bash
# --- Basic Usage ---
# Scan current directory (Plain text)
locr
python locr.py

# Scan a specific folder with Color
locr src --color
python locr.py src -c

# --- Output to File ---
# Scan 'src' and save to 'src/src_locr.txt'
locr src -o
python locr.py src -o

# Scan current dir and save to 'current_folder_locr.txt'
locr -o
python locr.py -o

# Scan 'src' but save to a specific file in current location
locr src -o my_report.txt
python locr.py src -o my_report.txt

# --- Raw / Debug Mode ---
locr --raw
```

## Troubleshooting

  - **"Command not found":** Ensure you ran `pip install -e .` inside the folder. If it still fails, make sure your Python `Scripts/` (Windows) or `bin/` (Mac/Linux) folder is in your system PATH.
  - **Spinner not showing:** The spinner is automatically disabled if you are piping output to a file or if the terminal does not support TTY.
  - **Colors not showing:** You must explicitly add the `-c` or `--color` flag.

## FAQ

### 1\. Will `locr` eat my RAM?

**No.** `locr` processes files using a "stream" method (line-by-line). It does not load entire files into memory. Whether you scan a 10-line script or a 10-million-line monolith, the memory usage remains negligible.

### 2\. Is it safe to run on my main User directory?

**Yes, but it might take a while.** `locr` is Read-Only. It never modifies files. However, scanning your entire User folder (which lacks a `.gitignore`) means checking every single file.

  * **Tip:** Use `Ctrl+C` to stop it if it takes too long. `locr` will handle this gracefully and show you the **partial results** found up to that point.

### 3\. Will it crash on binary files?

**No.** `locr` uses a strict extension whitelist. It only opens files with known source code extensions (`.py`, `.js`, etc.). It automatically ignores images, EXEs, and zips.

### 4\. What if I don't have a `.gitignore` file?

**No problem.** `locr` has a built-in "safety list". It automatically ignores heavy folders like `node_modules`, `.git`, `dist`, `venv`, and `__pycache__`, even if your project is completely unconfigured.

### 5\. Does it send my code anywhere?

**No.** `locr` runs 100% locally. You can audit the source code in `locr.py`—it uses standard Python libraries only.

### 6\. Is the count 100% compiler-accurate?
**It is a close estimate.** `locr` uses a heuristic "scanner" rather than a full compiler parser.
* **Pros:** It is blazing fast and supports many languages easily.
* **Cons:** It might occasionally miscount a comment symbol if it appears inside a string (e.g., `print("Rank #1")`).
For 99% of use cases, this margin of error is negligible.

### 7\. Why is the second run faster?

Your Operating System caches file locations in RAM after the first run. `locr` takes advantage of this "Warm Cache" to fly through directories instantly on subsequent runs.

## ⚡ Performance: Cold vs. Warm Start

`locr` leverages your Operating System's file system cache to deliver near-instant results on repeat scans.

**The Benchmark:** Scanning the **Django** repository (~3,500 files, ~400,000 lines of code).
```bash
# Clone the Django repo (depth-1)
git clone --depth 1 https://github.com/django/django.git

# run locr
locr django
```

### 🥶 1. Cold Start (First Run)
*State: Fresh clone, OS file cache empty. The script must wait for the physical hard drive to read every file.*

```
===========================================================================
Language                    Files        Blank      Comment         Code
---------------------------------------------------------------------------
Python                       2884        67496        66005       372533
JavaScript                    113         4821         4030        20362
HTML                          372          547            0         5077
CSS                            48          998          154         4425
JSON                           54            3            0         1808
YAML                           18           84           10          954
XML                            14            0            0          230
Markdown                        8           43            0          135
Shell                           3           35           13           92
TOML                            1            8            0           60
---------------------------------------------------------------------------
TOTAL                        3515        74035        70212       405676
===========================================================================
Processed 3515 files in 40.718 seconds.
```
### 🔥 2. Warm Start (Second Run)
State: Files are now cached in System RAM. The bottleneck shifts from Disk I/O to pure CPU processing.

```
===========================================================================
Language                    Files        Blank      Comment         Code
---------------------------------------------------------------------------
Python                       2884        67496        66005       372533
JavaScript                    113         4821         4030        20362
HTML                          372          547            0         5077
CSS                            48          998          154         4425
JSON                           54            3            0         1808
YAML                           18           84           10          954
XML                            14            0            0          230
Markdown                        8           43            0          135
Shell                           3           35           13           92
TOML                            1            8            0           60
---------------------------------------------------------------------------
TOTAL                        3515        74035        70212       405676
===========================================================================
Processed 3515 files in 1.175 seconds.
```
>Note: The 40s -> 1s jump demonstrates that locr is lightweight enough to keep up with your RAM. The initial delay is purely your Disk I/O waking up.


### ❄️ When will caching NOT work?
Since `locr` relies on your Operating System's RAM cache (Page Cache), you will experience a slow **Cold Start** again if:

1.  **You Reboot your Computer:** RAM is volatile. When you restart, the cache is wiped.
2.  **You Run Heavy Applications:** If you open a AAA game or heavy video editor, Windows/Linux will flush the file cache to free up RAM for that application.
3.  **You Re-clone the Repo:** If you delete the folder and `git clone` it again, the OS treats them as brand new files on the disk.
4.  **You Use a Network Drive:** Scanning files on a NAS or mounted drive (`Z:\`) is limited by network latency, not just disk speed. Caching is often less effective here.


## 🚀 Roadmap & Future Improvements

`locr` is an active project. The goal is to maintain the "Zero Dependency" philosophy while improving accuracy and speed.

* **Nested `.gitignore` Support:** Currently, only the root `.gitignore` is respected. Future updates will support recursive ignore files inside subdirectories.
* **Parallel Processing:** I plan to implement `concurrent.futures` to parallelize file reading, significantly speeding up scans on multi-core machines.
* **JSON Output:** Adding a `--json` flag to export machine-readable data for use in CI/CD pipelines or dashboards.
* **Better Tokenization:** Moving from heuristic scanning to a robust tokenizer to better handle edge cases (like comment symbols inside string literals).
* **Unit Tests:** Adding a comprehensive `unittest` suite to guarantee stability.
