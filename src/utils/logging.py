"""
Logging estructurado para el pipeline CODEFEST AD ASTRA.

Uso:
    from src.utils.logging import get_logger
    log = get_logger(__name__)
    log.info("mensaje")
"""
from __future__ import annotations

import logging
import sys


_CONFIGURED = False


def _configure_root() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    root = logging.getLogger("codefest")
    root.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    root.addHandler(handler)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root()
    return logging.getLogger(f"codefest.{name}")
