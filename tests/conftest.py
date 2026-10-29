from pathlib import Path
import tempfile


def pytest_configure(config):
    path=Path(__file__).resolve().parents[1] / '.tmp'
    path.mkdir(exist_ok=True)
    tempfile.tempdir=str(path)
