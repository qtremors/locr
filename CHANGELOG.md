# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## [1.0.0] - 2025-12-04

### Added
- **CLI Support**: Added `setup.py` configuration to install the tool globally via `pip`.
- **Command Entry Point**: The tool can now be run using the command `locr` from any terminal location.
- **Language Colors**: Added distinct color mappings for major languages (Python=Yellow, Web=Red/Blue, Systems=Cyan).
- **Smart Output**: Added `-o` flag logic. If no filename is provided, it saves the report *inside* the scanned directory using the format `[folder]_locr.txt`.
- **Visual Feedback**: Added a lightweight loading spinner (`| / - \`) that provides feedback during large scans without impacting I/O performance.
- **Eager Pruning**: Implemented advanced `os.walk` manipulation to skip ignored directories *before* entering them.
- **Graceful Interrupts**: Added handling for `Ctrl+C`. The script no longer crashes but displays a warning (`⚠ Scan interrupted`) and outputs the statistics collected up to that point.
- **Partial Results**: The results table is now generated even if the scan is stopped early, allowing for quick checks on massive repositories.

### Changed
- **Performance**: Optimized the ignore logic to be "Eager". This reduced scan times on large repositories (e.g., those with `node_modules`) from ~7s to <0.1s.
- **Color Behavior**: Colors are now **opt-in** via the `-c` flag (previously on by default). This ensures cleaner output when piping to other tools.
- **Timer Accuracy**: The execution timer now measures wall-clock time from the exact moment of script start to final render.

### Fixed
- Fixed issues with terminal flashing on Windows CMD/PowerShell by rate-limiting the spinner updates.
- Fixed absolute path handling when generating automatic output filenames.
