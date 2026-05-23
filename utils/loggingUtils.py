import logging
import platform
import sys
from colorama import Fore, just_fix_windows_console
from utils.enums import ServiceName

if platform.system() == "Windows":
    just_fix_windows_console()

class CustomFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "service_name"):
            record.service_name = "MAIN"
        return True

class CustomFormatter(logging.Formatter):
    fmt = "%(asctime)s [%(service_name)s] | [%(levelname)s]: %(message)s"

    FORMATS = {
        logging.DEBUG: Fore.LIGHTBLACK_EX + fmt + Fore.RESET,
        logging.INFO: Fore.WHITE + fmt + Fore.RESET,
        logging.WARNING: Fore.YELLOW + fmt + Fore.RESET,
        logging.ERROR: Fore.LIGHTRED_EX + fmt + Fore.RESET,
        logging.CRITICAL: Fore.RED + fmt + Fore.RESET
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class ApplicationLogger:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    def mdl_print(self, text, error=False):
        if not error:
            self.logger.info(text, extra={"service_name": ServiceName.MOODLE})
        else:
            self.logger.error(text, extra={"service_name": ServiceName.MOODLE})

    def dc_print(self, text, error=False):
        if not error:
            self.logger.info(text, extra={"service_name": ServiceName.DISCORD})
        else:
            self.logger.error(text, extra={"service_name": ServiceName.DISCORD})

    def dl_print(self, text, error=False):
        if not error:
            self.logger.info(text, extra={"service_name": ServiceName.DOWNLOADER})
        else:
            self.logger.error(text, extra={"service_name": ServiceName.DOWNLOADER})

def prepare_logger(logger: logging.Logger) -> logging.Logger:
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    logger.addFilter(CustomFilter())
    logger.addHandler(handler)
    return logger
