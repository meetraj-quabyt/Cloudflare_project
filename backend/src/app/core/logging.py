import logging
import sys


def setup_logging():
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root.addHandler(handler)
    root.setLevel(logging.INFO)


class _Logger:
    def __init__(self, name):
        self._l = logging.getLogger(name)
    def _fmt(self, msg, kwargs):
        if kwargs:
            return msg + " " + " ".join(f"{k}={v}" for k, v in kwargs.items())
        return msg
    def info(self, msg, *a, **kw):
        self._l.info(self._fmt(msg, kw), *a)
    def warning(self, msg, *a, **kw):
        self._l.warning(self._fmt(msg, kw), *a)
    def error(self, msg, *a, **kw):
        self._l.error(self._fmt(msg, kw), *a)
    def debug(self, msg, *a, **kw):
        self._l.debug(self._fmt(msg, kw), *a)


def get_logger(name: str):
    return _Logger(name)