import tempfile
import zipfile
import hashlib

from pathlib import Path

from core.transfer import create_project_archive


def test_transfer():

    with tempfile.TemporaryDirectory() as temp:

        root = Path(temp)

        project = root / "ExampleProject"
        project.mkdir()

        (project / "main.py").write_text(
            "print('Hello Termux2PC')"
        )

        src = project / "src"
        src.mkdir()

        (src / "engine.cpp").write_text(
            "int main() { return 0; }"
        )

        git = project / ".git"
        git.mkdir()

        (git / "config").write_text(
            "temporary data"
        )

        archive_path = root / "ExampleProject.zip"

        result = create_project_archive(
            project,
            archive_path
        )

        # Verificar quantidade de arquivos
        assert result["files"] == 2

        # Verificar existência do ZIP
        assert archive_path.exists()

        # Verificar estrutura do ZIP
        with zipfile.ZipFile(archive_path, "r") as archive:

            names = archive.namelist()

            assert "main.py" in names
            assert "src/engine.cpp" in names

            assert not any(
                ".git" in name for name in names
            )

        # Calcular SHA-256 independentemente
        with open(archive_path, "rb") as file:
            expected_hash = hashlib.sha256(
                file.read()
            ).hexdigest()

        # Comparar hashes
        assert len(result["sha256"]) == 64

        assert result["sha256"] == expected_hash

        print("Transfer test: PASSED")
        print("Files:", result["files"])
        print("ZIP size:", result["size"], "bytes")
        print("SHA-256:", result["sha256"])
        print("Integrity test: PASSED")


if __name__ == "__main__":
    test_transfer()
