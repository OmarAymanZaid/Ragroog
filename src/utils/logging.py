from __future__ import annotations

import sys
from typing import Any

from loguru import logger


def configure_logging(level: str = "INFO") -> None:
    """Configures Loguru for structured, high-performance logging.
    
    This clears out default interceptors and pipes everything cleanly
    to standard output.
    """
    logger.remove()
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        backtrace=False,
        diagnose=False,
    )


def bind_context(**kwargs: Any) -> Any:
    """Return a logger bound with the given context keys.

    Typical use: ``log = bind_context(session_id=sid, stage="retrieve")``.
    """
    return logger.bind(**kwargs)