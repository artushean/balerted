from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_alerts.config import load_settings
from stock_alerts.scanner import MomentumScanner


def test_watchlist_add_remove(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    (tmp_path / "medium_cap.txt").write_text("AAPL\n")
    (tmp_path / "large_cap.txt").write_text("MSFT\n")

    settings = load_settings()
    scanner = MomentumScanner(settings)

    scanner.add_watch("msft", "note")
    items = scanner.get_watchlist()
    assert any(i.symbol == "MSFT" for i in items)

    scanner.remove_watch("MSFT")
    items = scanner.get_watchlist()
    assert all(i.symbol != "MSFT" for i in items)
