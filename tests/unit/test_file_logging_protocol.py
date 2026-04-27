from __future__ import annotations

from pathlib import Path

from prompt_autoresearch.console.file_logging_protocol import FileLogger


def test_file_logger_appends_to_existing_file(tmp_path: Path) -> None:
    log_path = tmp_path / "session.log"
    log_path.write_text("existing line\n")

    logger = FileLogger(log_path)
    logger.report_message("new line")

    assert log_path.read_text() == "existing line\nnew line\n"
