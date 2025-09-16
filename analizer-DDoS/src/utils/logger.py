import logging
from logging.handlers import RotatingFileHandler
import sys

def get_logger(name: str, logfile: str | None = None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Consola
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        # (Opcional) fichero rotativo
        if logfile:
            fh = RotatingFileHandler(logfile, maxBytes=1_000_000, backupCount=3)
            fh.setFormatter(fmt)
            logger.addHandler(fh)

    return logger