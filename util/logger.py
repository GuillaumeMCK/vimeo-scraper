from logging import Formatter, Logger, StreamHandler, FileHandler
from logging import addLevelName, setLoggerClass, getLogger, basicConfig
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL

from sys import stdout

LOGFILE = 'log.txt'
# ANSI escape code to stylize text
_RESET = '\33[0m'
_BOLD = '\33[1m'
_RED = '\33[38;2;241;70;55m'
_GREEN = '\33[38;2;88;255;131m'
_BLUE = '\33[38;2;59;142;234m'
_MAGENTA = '\33[38;2;185;96;208m'
_YELLOW = '\33[38;2;200;200;0m'
_GRAY = '\33[38;2;204;204;204m'
# Custom levels
STAT_INFO = 11
SUCC_INFO = 12
FAIL_INFO = 13
# Log Formats
_FMT = "{message}"
_FORMATS = {
    DEBUG: f'[{_BOLD + _GRAY}DEBUG{_RESET}] {_FMT}',
    STAT_INFO: f'[{_MAGENTA}x{_RESET}] {_FMT}',
    SUCC_INFO: f'[{_BOLD + _GREEN}+{_RESET}] {_FMT}',
    FAIL_INFO: f'[{_BOLD + _RED}-{_RESET}] {_FMT}',
    INFO: f'[{_BOLD + _BLUE}*{_RESET}] {_FMT}',
    WARNING: f'[{_BOLD + _YELLOW}!{_RESET}] {_FMT}',
    ERROR: f'[{_RED}ERROR{_RESET}] {_FMT}',
    CRITICAL: f'[{_RED}CRITICAL{_RESET}] {_FMT}',
}


class NiceFormatter(Formatter):
    def format(self, record):
        log__fmt = _FORMATS[record.levelno]
        formatter = Formatter(log__fmt, style="{")
        return formatter.format(record)


class NiceLogger(Logger):
    # Custom logger class
    def __init__(self, name, level=INFO):
        Logger.__init__(self, name, level)

        addLevelName(STAT_INFO, "STATUS")
        addLevelName(SUCC_INFO, "SUCCESS")
        addLevelName(FAIL_INFO, "FAILURES")

    def status(self, msg, *args, **kwargs):
        # Add status log methode
        if self.isEnabledFor(STAT_INFO):
            self._log(STAT_INFO, msg, args, **kwargs)

    def success(self, msg, *args, **kwargs):
        # Add success log methode
        if self.isEnabledFor(SUCC_INFO):
            self._log(SUCC_INFO, msg, args, **kwargs)

    def failure(self, msg, *args, **kwargs):
        # Add failure log methode
        if self.isEnabledFor(FAIL_INFO):
            self._log(FAIL_INFO, msg, args, **kwargs)


def setup_logger(name, loglevel=DEBUG) -> Logger:
    # Set up logger and add handlers
    setLoggerClass(NiceLogger)

    logger = getLogger(name)
    logger.setLevel(loglevel)

    stdout_handler_formatter = NiceFormatter()
    file_handler_formatter = Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    stdout_handler = StreamHandler(stream=stdout)
    stdout_handler.setFormatter(stdout_handler_formatter)

    file_handler = FileHandler(filename=LOGFILE)
    file_handler.setFormatter(file_handler_formatter)

    basicConfig(
        # Define logging level
        level=DEBUG,
        # Declare handlers
        handlers=[
            file_handler,
            stdout_handler
        ],
    )
    return logger


log = setup_logger(__name__)

if __name__ == "__main__":
    log.debug("a")
    log.status("b")
    log.success("c")
    log.failure("d")
    log.info("e")
    log.warning("f")
    log.error("g")
    log.critical("h")
