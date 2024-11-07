import logging
import os
from config.env import Env

logger = logging.getLogger(__name__)

class PackagePathFilter(logging.Filter):
    def __init__(self, base_path_to_remove: str) -> None:
        self.base_path_to_remove = base_path_to_remove
        super().__init__()

    def filter(self, record):
        record.pathname = record.pathname.replace(f"{self.base_path_to_remove}/", "")
        return True

def setupLogger():
    """
    call this function in main the main script
    """
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.propagate = False

    # custom formatting stream handler
    logger_stream_handler = logging.StreamHandler()
    logger_stream_handler.setLevel(logging.DEBUG if Env.DEBUG else logging.INFO)
    logger_stream_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: \033[92m[%(pathname)s@%(funcName)s():%(lineno)d] %(message)s\033[0m",
            datefmt="%d-%m-%Y %H:%M:%S",
        )
    )
    logger_stream_handler.addFilter(PackagePathFilter(base_path_to_remove=os.getcwd()))
    logger.addHandler(logger_stream_handler)