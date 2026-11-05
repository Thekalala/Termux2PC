
import tempfile

from pathlib import Path

from client.android import prepare_project


def test_android_client():

    with tempfile.TemporaryDirectory() as temp:

        root = Path(temp)

        project = root / "TestProject"
        project.mkdir()

        (project / "main.py").write_text(
            "print('Termux2PC')"
        )

        (project / "engine.cpp").write_text(
            "int main() { return 0; }"
        )

        result = prepare_project(project)

        assert result["project"] == "TestProject"

        assert result["total_files"] == 2

        assert result["languages"]["Python"] == 1

        assert result["languages"]["C++"] == 1

        assert Path(result["archive"]).exists()

        assert len(result["sha256"]) == 64

        print("Android client test: PASSED")
        print("Project:", result["project"])
        print("Files:", result["total_files"])
        print("Languages:", result["languages"])
        print("SHA-256:", result["sha256"])


if __name__ == "__main__":
    test_android_client()
