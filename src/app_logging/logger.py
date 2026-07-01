"""Logging helpers for deterministic, structured pipeline logs."""

from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure global logging format for pipeline execution.

    This function can be called at process startup to standardize log output
    across modules and tests.
    """

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
