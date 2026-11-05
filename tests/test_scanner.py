
import tempfile

from pathlib import Path
from core.scanner import scan_project


def test_scanner():

    with tempfile.TemporaryDirectory() as temp:

        root = Path(temp)

        (root / "main.py").write_text(
            "print('Hello')"
        )

        (root / "engine.cpp").write_text(
            "int main() { return 0; }"
        )

        (root / "Cargo.toml").write_text(
            "[package]"
        )

        result = scan_project(root)

        assert result["total_files"] == 3

        assert result["languages"]["Python"] == 1

        assert result["languages"]["C++"] == 1

        assert result["languages"]["Other"] == 1

        print("Scanner test: PASSED")


if __name__ == "__main__":
    test_scanner()
