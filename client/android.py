
import os
import re
import requests

from pathlib import Path

from core.scanner import scan_project
from core.transfer import create_project_archive


STORAGE = Path.home() / "Termux2PC" / "storage"


def get_config():
    token = os.environ.get("TERMUX2PC_TOKEN")
    pc_address = os.environ.get(
        "TERMUX2PC_PC",
        "http://192.168.0.3:8765"
    )

    if not token:
        raise RuntimeError("TERMUX2PC_TOKEN is not configured")

    return pc_address.rstrip("/"), token


def validate_project_name(name):
    if not isinstance(name, str):
        raise ValueError("Invalid project name")

    if not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", name):
        raise ValueError("Invalid project name")

    return name


def prepare_project(project_path):
    project_path = Path(project_path).expanduser().resolve()

    report = scan_project(project_path)

    STORAGE.mkdir(parents=True, exist_ok=True)

    archive_path = STORAGE / f"{report['name']}.zip"

    package = create_project_archive(
        project_path,
        archive_path
    )

    return {
        "project": report["name"],
        "total_files": report["total_files"],
        "languages": report["languages"],
        "archive": package["archive"],
        "size": package["size"],
        "sha256": package["sha256"]
    }


def send_project(package, pc_address=None, token=None):
    default_address, default_token = get_config()

    pc_address = (pc_address or default_address).rstrip("/")
    token = token or default_token

    project_name = validate_project_name(package["project"])
    archive_path = Path(package["archive"])

    if not archive_path.is_file():
        raise FileNotFoundError("Project archive not found")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    data = {
        "project_name": project_name,
        "sha256": package["sha256"]
    }

    with archive_path.open("rb") as file:
        response = requests.post(
            pc_address + "/upload",
            headers=headers,
            data=data,
            files={
                "file": (
                    archive_path.name,
                    file,
                    "application/zip"
                )
            },
            timeout=(10, 300)
        )

    response.raise_for_status()

    return response.json()


def request_run(project_name, pc_address=None, token=None):
    default_address, default_token = get_config()

    pc_address = (pc_address or default_address).rstrip("/")
    token = token or default_token

    project_name = validate_project_name(project_name)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        pc_address + "/run",
        headers=headers,
        json={"project": project_name},
        timeout=(10, 30)
    )

    response.raise_for_status()

    return response.json()


def deploy_and_run(project_path):
    print("[1/5] Preparing project...")

    package = prepare_project(project_path)

    print("[2/5] Package ready")
    print("[3/5] Sending project to Windows...")

    upload_result = send_project(package)

    if upload_result.get("status") != "success":
        raise RuntimeError("Upload was not confirmed")

    print("[4/5] Upload confirmed")
    print("[5/5] Requesting execution...")

    execution_result = request_run(package["project"])

    return {
        "upload": upload_result,
        "execution": execution_result
    }
