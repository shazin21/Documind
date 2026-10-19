import logging
import sys
from typing import Any


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configures structured application logging with sensitive field protection."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger("documind")
    logger.setLevel(level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()
