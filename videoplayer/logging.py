from logging import getLogger, Formatter, StreamHandler, INFO, Logger
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: str | None = None, log_level: int = INFO) -> Logger:
    """
    Set up a structured logging system and return the named logger.

    Args:
        log_file: Optional path to a log file. If None, console logging only.
        log_level: Logging level (default: INFO)
    """
    logger = getLogger("videoplayer")
    logger.setLevel(log_level)

    # Prevent double logging when called multiple times
    if logger.hasHandlers():
        return logger

    formatter = Formatter(
        fmt="[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    console_handler = StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            filename=log_file, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
