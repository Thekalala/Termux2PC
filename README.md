# Termux2PC

**Deploy Python projects from Android (Termux) to Windows over a local network.**

Termux2PC is an experimental deployment and remote execution tool that connects an Android device running Termux to a Windows computer.

It allows developers to scan, package, transfer, verify, and request execution of explicitly authorized Python projects.

**Version:** 0.4.2
**Status:** Experimental

---

## Features

### Project management

- Project directory scanning.
- Programming language detection.
- File counting and project reports.

### Packaging and transfer

- Automatic ZIP packaging.
- SHA-256 checksum generation.
- HTTP project transfer.
- Archive integrity verification.
- Bearer-token authentication.

### Windows server

- Starlette and Uvicorn HTTP server.
- Project upload endpoint.
- Project execution endpoint.
- Health endpoint.
- 250 MB upload limit.
- ZIP validation and path traversal protection.
- Project name validation.

### Remote execution

- Execution requests for uploaded projects.
- Explicit project allowlist.
- Python execution through `main.py`.
- Standard output and standard error capture.
- Execution status and exit code.
- Execution timeout.

### Command-line interface

- Deploy projects from Termux.
- Request execution of previously uploaded projects.
- Display server responses.

---

## Architecture

    ANDROID / TERMUX
           |
       Termux2PC CLI
           |
      Project Scanner
           |
       ZIP Packaging
           |
       SHA-256 Hash
           |
       HTTP Transfer
           |
      LOCAL NETWORK
           |
      WINDOWS SERVER
           |
      Starlette API
        /       \
     Upload    Execution
       |          |
    ZIP Check  Allowlist
       |          |
   Extraction Python Runner
       |          |
       +----+-----+
            |
      Execution Result
            |
         TERMUX CLI

---

## Project structure

    Termux2PC/
    ├── .gitignore
    ├── LICENSE
    ├── cli.py
    ├── client/
    │   ├── __init__.py
    │   └── android.py
    ├── core/
    │   ├── __init__.py
    │   ├── scanner.py
    │   ├── security.py
    │   └── transfer.py
    ├── server/
    │   ├── __init__.py
    │   └── main.py
    ├── storage/
    │   └── .gitkeep
    ├── tests/
    │   ├── __init__.py
    │   ├── test_android_client.py
    │   ├── test_scanner.py
    │   └── test_transfer.py
    ├── requirements.txt
    └── README.md

The Windows installation also requires its own execution runner and approved-project configuration. These are configured on the Windows computer, not supplied as part of the Android CLI directory.
---

## Requirements

### Android

- Android device.
- Termux.
- Python 3.
- Access to the same local network as the Windows computer.

### Windows

- Windows computer.
- Python 3.
- Network access from the Android device.
- Termux2PC server installation.

### Python dependencies

Install the dependencies with:

    pip install -r requirements.txt

Dependencies:

- Starlette
- Uvicorn
- python-multipart
- Requests

---

## Installation

Clone the repository:

    git clone https://github.com/Thekalala/Termux2PC.git

Enter the project directory:

    cd Termux2PC

Install dependencies:

    pip install -r requirements.txt

---

## Windows server setup

Start the server from the Windows installation directory.

Configure the authentication token in PowerShell:

    $env:TERMUX2PC_TOKEN = Read-Host "Enter the Termux2PC token"

Start the server:

    python -m uvicorn server.main:app --host 0.0.0.0 --port 8765

The server listens on port 8765.

The Windows firewall must allow the connection on the trusted local network.

The server must be configured with the same token used by the Android client.

---

## Android configuration

Configure the Windows computer's local IP address:

    export TERMUX2PC_PC="http://WINDOWS_IP:8765"

Configure the same private authentication token:

    export TERMUX2PC_TOKEN="YOUR_PRIVATE_TOKEN"

Replace the example values with your actual configuration.

Do not commit credentials or private tokens to Git.

For persistent configuration, use a local environment file or your shell profile. Keep private configuration files out of version control.

---

## Usage

### Deploy a project

Pass the path to the project directory:

    python cli.py deploy ./my_project

The deployment process:

1. Scans the selected project.
2. Detects programming languages.
3. Creates a ZIP archive.
4. Calculates the SHA-256 checksum.
5. Uploads the archive to Windows.
6. Requests execution of the uploaded project.
7. Returns upload and execution results.

### Run an existing project

Request execution of a previously uploaded project:

    python cli.py run my_project

The project must be explicitly authorized by the Windows runner.

### CLI help

    python cli.py --help

Currently supported commands:

- `deploy`
- `run`

---

## Project authorization

Termux2PC uses an explicit project allowlist on the Windows side.

A project must be authorized by the Windows runner before execution is permitted.

The runner executes the project's `main.py` file using the Windows Python interpreter.

The allowlist is an authorization mechanism. It does not provide operating-system-level isolation.

Only authorize projects whose source code has been reviewed.

---

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Server status |
| POST | `/upload` | Upload a project archive |
| POST | `/run` | Request execution of an approved project |

Protected endpoints require the configured Bearer token.

---

## Security

Implemented controls include:

- Bearer-token authentication.
- SHA-256 archive integrity verification.
- Project name validation.
- ZIP archive validation.
- ZIP path traversal protection.
- Upload size limit.
- Explicit execution allowlist.
- Execution timeout.
- Restricted environment variables for child processes.

### Security limitations

Termux2PC is an experimental development tool, not a security sandbox.

- Python projects execute with the permissions of the Windows user running the server.
- The allowlist is an authorization mechanism, not a sandbox.
- HTTP communication is not encrypted.
- Use only on a trusted local network.
- Do not expose the server directly to the public internet.
- Do not configure public port forwarding.
- Only authorize reviewed source code.
- Output truncation does not guarantee a strict memory limit.
- Execution timeout does not necessarily terminate every child process.
- Concurrent uploads may consume temporary disk space.

Do not use this version to execute untrusted code or expose the server to untrusted networks.

---

## Testing

Run the available test modules from the project root:

    python -m tests.test_scanner

    python -m tests.test_transfer

    python -m tests.test_android_client

Compile the main Python modules:

    python -m py_compile cli.py client/android.py server/main.py core/scanner.py core/transfer.py

These tests cover selected project scanning, transfer, and Android client functionality. They do not constitute a complete security audit.

---

## Roadmap

The following features are planned and are not claimed as implemented in version 0.4.2.

### Remote Execution 2.0

- Background task execution.
- Unique task identifiers.
- Task status tracking.
- Execution history.
- Live logs.
- Task cancellation.

### Monitoring

- CPU usage.
- RAM usage.
- Disk usage.
- Network statistics.
- Process monitoring.

### Dashboard

- Remote operations interface.
- Task management.
- Execution logs.
- Project history.
- Multiple computer management.

### Advanced deployment

- Project versioning.
- Deployment rollback.
- Dependency validation.
- Automated testing before deployment.

### Multi-language support

- C and C++.
- Rust.
- Java.
- JavaScript and Node.js.
- Go.

### Security improvements

- HTTPS support.
- Stronger process isolation.
- Resource limits.
- Process-tree termination.
- Improved upload concurrency control.
- Audit logs.

---

## Version

**Current version:** 0.4.2

Termux2PC is under active development. Features and interfaces may change.

---

## License

Termux2PC is licensed under the MIT License.

You are free to use, copy, modify, distribute, sublicense, and use this
software commercially, subject to the conditions in the `LICENSE` file.

See [LICENSE](LICENSE) for the complete license text.

---

## Disclaimer

Termux2PC is provided for development and educational purposes.

Users are responsible for reviewing projects before authorizing their execution and for securing their local network environment.

The authors are not responsible for damage caused by executing untrusted code or insecure deployment configurations.

---

## Author

**Thekalala**

GitHub: https://github.com/Thekalala
