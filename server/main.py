
import os
import re
import hmac
import hashlib
import zipfile
import shutil
import uuid
import stat
import asyncio
import tempfile

from pathlib import Path, PurePosixPath

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
RECEIVED_DIR = STORAGE_DIR / "received"
TEMP_DIR = STORAGE_DIR / "temp"

MAX_UPLOAD = 250 * 1024 * 1024
MAX_UNPACKED = 1024 * 1024 * 1024
MAX_FILES = 20000
MAX_FIELDS = 5

TOKEN = os.environ.get("TERMUX2PC_TOKEN")

if not TOKEN:
    raise RuntimeError("TERMUX2PC_TOKEN is required")

RECEIVED_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def authenticate(request):
    authorization = request.headers.get("authorization")
    expected = f"Bearer {TOKEN}"

    return bool(
        authorization
        and hmac.compare_digest(authorization, expected)
    )


def validate_project_name(name):
    return (
        isinstance(name, str)
        and bool(re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", name))
    )


def safe_extract(archive, destination):
    destination = Path(destination).resolve()

    with zipfile.ZipFile(archive, "r") as zf:
        infos = zf.infolist()

        if len(infos) > MAX_FILES:
            raise ValueError("Too many files")

        total_size = sum(info.file_size for info in infos)

        if total_size > MAX_UNPACKED:
            raise ValueError("Archive too large")

        seen = set()
        file_paths = set()
        directory_paths = set()

        for info in infos:
            name = info.filename

            if "\\" in name or "\x00" in name:
                raise ValueError("Invalid archive path")

            member = PurePosixPath(name)

            if member.is_absolute() or ".." in member.parts:
                raise ValueError("Unsafe archive path")

            if any(":" in part for part in member.parts):
                raise ValueError("Invalid path")

            if not member.parts:
                raise ValueError("Empty archive path")

            normalized = member.as_posix().casefold()

            if normalized in seen:
                raise ValueError("Duplicate archive path")

            seen.add(normalized)

            mode = info.external_attr >> 16
            file_type = stat.S_IFMT(mode)

            if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise ValueError("Unsupported file type")

            is_directory = info.is_dir()

            if file_type == stat.S_IFDIR and not is_directory:
                raise ValueError("Invalid directory entry")

            if file_type == stat.S_IFREG and is_directory:
                raise ValueError("Invalid file entry")

            if info.flag_bits & 0x1:
                raise ValueError("Encrypted ZIP not supported")

            if info.file_size > 0:
                if info.compress_size == 0:
                    raise ValueError("Invalid compression")

                if info.file_size / info.compress_size > 1000:
                    raise ValueError("Suspicious compression ratio")

            if is_directory:
                directory_paths.add(normalized)
            else:
                file_paths.add(normalized)

            target = destination.joinpath(*member.parts).resolve()

            if not target.is_relative_to(destination):
                raise ValueError("Path traversal detected")

        for file_path in file_paths:
            parts = file_path.split("/")

            for index in range(1, len(parts)):
                parent = "/".join(parts[:index])

                if parent in file_paths:
                    raise ValueError("File-directory conflict")

        if file_paths & directory_paths:
            raise ValueError("File-directory conflict")

        zf.extractall(destination)


def calculate_sha256(file_path):
    digest = hashlib.sha256()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


async def health(request):
    return JSONResponse({
        "application": "Termux2PC",
        "version": "0.4.2",
        "platform": "Windows",
        "status": "online"
    })


async def upload_project(request):
    if not authenticate(request):
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401
        )

    content_length = request.headers.get("content-length")

    if content_length:
        try:
            if int(content_length) > MAX_UPLOAD:
                return JSONResponse(
                    {"error": "Upload too large"},
                    status_code=413
                )
        except ValueError:
            return JSONResponse(
                {"error": "Invalid Content-Length"},
                status_code=400
            )

    archive_path = None
    staging_dir = None

    try:
        async with request.form(
            max_files=1,
            max_fields=MAX_FIELDS
        ) as form:

            uploaded_file = form.get("file")
            project_name = form.get("project_name")
            expected_hash = form.get("sha256")

            if uploaded_file is None:
                return JSONResponse(
                    {"error": "Missing file"},
                    status_code=400
                )

            if not validate_project_name(project_name):
                return JSONResponse(
                    {"error": "Invalid project name"},
                    status_code=400
                )

            if not isinstance(expected_hash, str) or not re.fullmatch(
                r"[a-fA-F0-9]{64}",
                expected_hash
            ):
                return JSONResponse(
                    {"error": "Invalid SHA-256"},
                    status_code=400
                )

            project_dir = RECEIVED_DIR / project_name

            if project_dir.exists():
                return JSONResponse(
                    {"error": "Project already exists"},
                    status_code=409
                )

            temp_id = uuid.uuid4().hex
            archive_path = TEMP_DIR / f"{temp_id}.zip"
            staging_dir = TEMP_DIR / temp_id

            received = 0

            with open(archive_path, "wb") as output:
                while True:
                    chunk = await uploaded_file.read(1024 * 1024)

                    if not chunk:
                        break

                    received += len(chunk)

                    if received > MAX_UPLOAD:
                        raise ValueError("Upload too large")

                    output.write(chunk)

            actual_hash = calculate_sha256(archive_path)

            if not hmac.compare_digest(
                actual_hash.lower(),
                expected_hash.lower()
            ):
                raise ValueError("SHA-256 mismatch")

            staging_dir.mkdir(parents=True)

            safe_extract(archive_path, staging_dir)

            if not any(staging_dir.iterdir()):
                raise ValueError("Empty project archive")

            try:
                staging_dir.rename(project_dir)
            except FileExistsError:
                return JSONResponse(
                    {"error": "Project already exists"},
                    status_code=409
                )

            return JSONResponse({
                "status": "success",
                "project": project_name,
                "sha256": actual_hash,
                "size": received
            })

    except ValueError as error:
        return JSONResponse(
            {"error": str(error)},
            status_code=400
        )

    except zipfile.BadZipFile:
        return JSONResponse(
            {"error": "Invalid ZIP archive"},
            status_code=400
        )

    finally:
        if archive_path and archive_path.exists():
            archive_path.unlink()

        if staging_dir and staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)


async def run_project_endpoint(request):
    if not authenticate(request):
        return JSONResponse(
            {"error": "Unauthorized"},
            status_code=401
        )

    try:
        data = await request.json()
    except ValueError:
        return JSONResponse(
            {"error": "Invalid JSON"},
            status_code=400
        )

    project_name = data.get("project") if isinstance(data, dict) else None

    if not validate_project_name(project_name):
        return JSONResponse(
            {"error": "Invalid project name"},
            status_code=400
        )

    try:
        from core.runner import run_project

        result = await asyncio.to_thread(
            run_project,
            project_name
        )

        return JSONResponse(result)

    except PermissionError as error:
        return JSONResponse(
            {"error": str(error)},
            status_code=403
        )

    except FileNotFoundError as error:
        return JSONResponse(
            {"error": str(error)},
            status_code=404
        )

    except TimeoutError:
        return JSONResponse(
            {"error": "Execution timed out"},
            status_code=408
        )

    except Exception:
        return JSONResponse(
            {"error": "Execution failed"},
            status_code=500
        )


class UploadLimitMiddleware:
    def __init__(self, app, max_size):
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope.get("path") != "/upload"
            or scope.get("method") != "POST"
        ):
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))

        authorization = headers.get(b"authorization", b"").decode(
            "latin-1"
        )

        expected = f"Bearer {TOKEN}"

        if not hmac.compare_digest(authorization, expected):
            await self.reject(send, 401, "Unauthorized")
            return

        content_length = headers.get(b"content-length")

        if content_length:
            try:
                if int(content_length) > self.max_size:
                    await self.reject(send)
                    return
            except ValueError:
                await self.reject(send, 400, "Invalid Content-Length")
                return

        body_file = tempfile.SpooledTemporaryFile(
            max_size=1024 * 1024,
            mode="w+b"
        )

        total = 0

        try:
            while True:
                message = await receive()

                if message["type"] == "http.disconnect":
                    return

                chunk = message.get("body", b"")
                total += len(chunk)

                if total > self.max_size:
                    await self.reject(send)
                    return

                body_file.write(chunk)

                if not message.get("more_body", False):
                    break

            body_file.seek(0)

            async def replay():
                chunk = body_file.read(65536)

                return {
                    "type": "http.request",
                    "body": chunk,
                    "more_body": bool(chunk)
                }

            await self.app(scope, replay, send)

        finally:
            body_file.close()

    async def reject(self, send, status=413, message="Upload too large"):
        import json

        body = json.dumps({"error": message}).encode("utf-8")

        await send({
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode())
            ]
        })

        await send({
            "type": "http.response.body",
            "body": body
        })


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/upload", upload_project, methods=["POST"]),
    Route("/run", run_project_endpoint, methods=["POST"])
]

starlette_app = Starlette(
    debug=False,
    routes=routes
)

app = UploadLimitMiddleware(
    starlette_app,
    MAX_UPLOAD
)
