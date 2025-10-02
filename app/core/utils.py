
import logging
from .config import LOG_PATH

def get_logger(name: str = "stockbot"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
        sh = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        fh.setFormatter(fmt); sh.setFormatter(fmt)
        logger.addHandler(fh); logger.addHandler(sh)
    return logger
