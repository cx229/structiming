import logging
import sys
from .types import TimeUnit


def _convert_to_unit(seconds: float, unit: TimeUnit) -> float:
    if unit == "ms":
        return seconds * 1000
    if unit == "s":
        return seconds
    if unit == "m":
        return seconds / 60
    if unit == "h":
        return seconds / 3600
    raise ValueError(f"Unknown time_unit: {unit}")


def _default_logger():
    logger = logging.getLogger("structiming")
    if not logger.handlers:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format="%(message)s",
        )
    return logger