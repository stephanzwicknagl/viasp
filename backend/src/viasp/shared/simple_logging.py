from enum import Enum


class Level(Enum):
    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4
    PLAIN = 5


def log(text: str, level=Level.INFO) -> None:
    if level == Level.ERROR:
        print(f"[ERROR] {text}")
    elif level == Level.WARN:
        print(f"[WARNING] {text}")
    elif level == Level.INFO:
        print(f"[INFO] {text}")
    elif level == Level.DEBUG:
        print(f"[ERROR] {text}")
    elif level == Level.TRACE:
        print(f"[ERROR] {text}")
    elif level == Level.PLAIN:
        print(text)
    else:
        print(text)


def error(text: str) -> None:
    log(text, Level.ERROR)


def warn(text: str) -> None:
    log(text, Level.WARN)


def info(text: str) -> None:
    log(text, Level.INFO)


def debug(text: str) -> None:
    log(text, Level.DEBUG)


def trace(text: str) -> None:
    log(text, Level.TRACE)

def plain(text: str) -> None:
    log(text, Level.PLAIN)
