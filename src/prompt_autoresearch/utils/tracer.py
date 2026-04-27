from __future__ import annotations

import uuid
from _io import TextIOWrapper, _WrappedBuffer
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

import structlog
from structlog.typing import Processor

from prompt_autoresearch.utils.common_paths import ensure_directory, logs_dir

log_file: TextIOWrapper[_WrappedBuffer]


def initialize_tracing(experiment_name: str, indent: int | None = None) -> None:
    global log_file
    json_renderer: Processor
    if indent is not None:
        json_renderer = structlog.processors.JSONRenderer(indent=indent, sort_keys=True)
    else:
        json_renderer = structlog.processors.JSONRenderer(sort_keys=True)

    ensure_directory(logs_dir(experiment_name))
    log_path: Path = logs_dir(experiment_name)
    log_file = log_path.open(mode="a", encoding="utf-8")

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
            json_renderer,
        ],
        logger_factory=structlog.WriteLoggerFactory(file=log_file),
    )


def initialize_request() -> str:
    req_id: str = f"req_{uuid.uuid4().hex}"
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=req_id,  # your custom ID
        start_time=datetime.now(),
    )
    return req_id


class StructLoggerProtocol(structlog.typing.BindableLogger, Protocol):
    def bind(self, **new_values: Any) -> StructLoggerProtocol: ...
    def info(self, event: str | None = None, **kw: Any) -> Any: ...
    def error(self, event: str | None = None, **kw: Any) -> Any: ...


@dataclass
class Tracer:
    logger: StructLoggerProtocol = field(default_factory=structlog.get_logger)

    def add_context(self, name: str, value: Any) -> None:
        self.logger = self.logger.bind(**{name: value})

    def add_multi_context(self, name: str, value: Any) -> None:
        current_context = dict(structlog.get_context(self.logger))
        existing_value = current_context.get(name)

        if existing_value is None:
            combined_value = [value]
        elif isinstance(existing_value, list):
            combined_value = [*existing_value, value]
        else:
            combined_value = [existing_value, value]

        self.logger = self.logger.bind(**{name: combined_value})

    def log(self, event_name: str) -> None:
        self.logger.info(event_name)

    def log_exception(
        self,
        exception: BaseException,
        event_name: str | None = None,
    ) -> None:
        self.logger.error(event_name, exc_info=exception)
