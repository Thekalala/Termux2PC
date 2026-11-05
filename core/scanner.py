
from pathlib import Path


LANGUAGES = {
    ".py": "Python",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".rs": "Rust",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".html": "HTML",
    ".css": "CSS"
}


def scan_project(project_path):
    root = Path(project_path).expanduser().resolve()

    if not root.is_dir():
        raise ValueError("Project directory not found")

    result = {
        "name": root.name,
        "total_files": 0,
        "languages": {},
        "files": []
    }

    ignored = {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "target",
        "build"
    }

    for path in root.rglob("*"):
        if any(part in ignored for part in path.parts):
            continue

        if not path.is_file():
            continue

        result["total_files"] += 1

        language = LANGUAGES.get(
            path.suffix.lower(),
            "Other"
        )

        result["languages"][language] = (
            result["languages"].get(language, 0) + 1
        )

        result["files"].append(
            str(path.relative_to(root))
        )

    return result
