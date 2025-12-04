"""
locr_config.py
Configuration file for locr.
Contains colors, language definitions, and default ignore patterns.
"""

# =============================================================================
# 1. Colors & Visuals
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


# =============================================================================
# 2. Default Ignored Directories
# =============================================================================
DEFAULT_IGNORE_PATTERNS = [
    # Version Control
    ".git",
    ".svn",
    ".hg",
    # IDEs
    ".idea",
    ".vscode",
    # Python
    "__pycache__",
    "venv",
    ".venv",
    "env",
    # Node / Web
    "node_modules",
    "bower_components",
    # Build Artifacts
    "dist",
    "build",
    "target",
    "bin",
    "obj",
]

# =============================================================================
# 3. Language Definitions
# =============================================================================
LANGUAGES = {
    # Python (Yellow)
    ".py": {
        "name": "Python",
        "color": Colors.YELLOW,
        "single": "#",
        "multi": ('"""', '"""'),
    },
    # Web (Red/Blue/Magenta)
    ".html": {
        "name": "HTML",
        "color": Colors.RED,
        "single": None,
        "multi": (""),
    },
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
    ".md": {
        "name": "Markdown",
        "color": Colors.WHITE,
        "single": None,
        "multi": (""),
    },
    ".yaml": {"name": "YAML", "color": Colors.CYAN, "single": "#", "multi": None},
    ".yml": {"name": "YAML", "color": Colors.CYAN, "single": "#", "multi": None},
    ".toml": {"name": "TOML", "color": Colors.CYAN, "single": "#", "multi": None},
    ".xml": {
        "name": "XML",
        "color": Colors.RED,
        "single": None,
        "multi": (""),
    },
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
