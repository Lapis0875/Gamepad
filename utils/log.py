import logging
from .dt_utils import get_current_dt


def __get_log_file_name() -> str:
    return f"logs/{get_current_dt().isoformat(timespec='seconds', sep='=').replace(':', '-')}.txt"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if len(logger.handlers) > 0:
        # Ensure logger does not have any duplicated handlers.
        return logger

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(__get_log_file_name(), mode='wt', encoding='utf-8')
    fmt = logging.Formatter(
        style='{',
        fmt='[{asctime}] [{levelname}] {name}: {message}'
    )
    console_handler.setFormatter(fmt)
    file_handler.setFormatter(fmt)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger
