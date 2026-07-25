"""
PRISM Voice Assistant — Structured Logger
Provides a rotating-file + console logger used across all modules.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.config import LOG_FILE, LOG_LEVEL


def get_logger(name: str) -> logging.Logger:
    """Return a named logger configured with file + console handlers."""
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured — avoid duplicate handlers on re-import
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Rotating file handler (5 MB × 3 backup files) ─────────────────────────
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    # ── Console handler ────────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
