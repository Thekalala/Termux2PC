
import zipfile
import hashlib

from pathlib import Path


def calculate_sha256(file_path):

    digest = hashlib.sha256()

    with open(file_path, "rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            digest.update(chunk)

    return digest.hexdigest()


def create_project_archive(project_path, output_path):

    project = Path(project_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()

    if not project.exists() or not project.is_dir():
        raise ValueError("Project directory not found")

    if output.exists() and output.is_dir():
        raise ValueError("Output must be a file")

    if output == project or project in output.parents:
        raise ValueError("Archive cannot be inside project")

    ignored = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "node_modules",
        "target",
        "build"
    }

    files_added = 0

    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED
    ) as archive:

        for file in project.rglob("*"):

            if not file.is_file():
                continue

            relative = file.relative_to(project)

            if any(part in ignored for part in relative.parts):
                continue

            archive.write(
                file,
                arcname=relative.as_posix()
            )

            files_added += 1

    file_hash = calculate_sha256(output)

    return {
        "project": project.name,
        "archive": str(output),
        "files": files_added,
        "size": output.stat().st_size,
        "sha256": file_hash
    }
