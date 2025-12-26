
import logging
from logging.handlers import RotatingFileHandler
import time
import os
from pathlib import Path
from typing import Optional
import traceback


class SafeFormatter(logging.Formatter):
    """
    Formatter that prints exceptions without reading source lines (skips linecache).
    This prevents recursion during traceback formatting on Python 3.13.

    If you ever want the classic behavior back, set EEJO_LOG_SAFE_EXC=0 to use
    the standard logging.Formatter for exception formatting.
    """
    def __init__(self, *args, safe_exc: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self._safe_exc = safe_exc

    def formatException(self, exc_info):
        if not self._safe_exc:
            # fall back to default behavior (may read source lines via linecache)
            return super().formatException(exc_info)

        # exc_info is (type, value, tb). Render without line lookups:
        _, exc_value, _ = exc_info
        tbe = traceback.TracebackException.from_exception(
            exc_value,
            lookup_lines=False,   # <-- avoids linecache / source reads
            capture_locals=False  # keep output small and deterministic
        )
        return ''.join(tbe.format())


class Logger:
    """
    Application-wide logger with rotating file handler and optional console output.

    Backward compatibility:
    - Exposes `Logger.app_log` as a configured `logging.Logger` instance.
    - Initializes once on import (same behavior as original).
    """
    # Public logger reference for existing imports
    app_log: logging.Logger

    # Defaults (can be overridden via env)
    _DEFAULT_LOGGER_NAME = "root"
    _DEFAULT_LEVEL = os.getenv("EEJO_LOG_LEVEL", "INFO").upper()  # INFO/DEBUG/WARNING/ERROR
    _ENABLE_CONSOLE = os.getenv("EEJO_LOG_CONSOLE", "0") in ("1", "true", "True")
    _USE_UTC_IN_FILENAME = os.getenv("EEJO_LOG_USE_UTC", "0") in ("1", "true", "True")
    _MAX_BYTES = int(os.getenv("EEJO_LOG_MAX_BYTES", str(5 * 1024 * 1024)))
    _BACKUP_COUNT = int(os.getenv("EEJO_LOG_BACKUP_COUNT", "2"))
    _LOG_DIR = os.getenv("EEJO_LOG_DIR")  # if not set, derive from package path

    # New: control SafeFormatter behavior (default ON)
    _SAFE_EXC = os.getenv("EEJO_LOG_SAFE_EXC", "1") in ("1", "true", "True")

    # Optional: hush internal logging diagnostics if desired
    # (This doesn't affect your app's own errors—only logging's internal ones.)
    _RAISE_INTERNAL_LOGGING_EXCEPTIONS = os.getenv("EEJO_LOG_RAISE_INTERNAL", "0") in ("1", "true", "True")

    # Internal singleton guard
    _initialized = False

    @classmethod
    def _resolve_log_dir(cls) -> Path:
        """
        Resolve the log directory:
        - EEJO_LOG_DIR env var (if provided)
        - default: <project_root>/Lib/Eejo_Log
        """
        if cls._LOG_DIR:
            return Path(cls._LOG_DIR).expanduser().resolve()
        # project_root is parent of this file's directory
        project_root = Path(__file__).resolve().parent.parent
        return project_root / "Lib" / "Eejo_Log"

    @classmethod
    def _timestamp(cls) -> str:
        t = time.gmtime() if cls._USE_UTC_IN_FILENAME else time.localtime()
        return time.strftime("%Y_%m_%d_%H_%M_%S", t)

    @classmethod
    def _build_log_path(cls) -> Path:
        log_dir = cls._resolve_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)  # ensure directory exists
        filename = f"Eejo_Timer_{cls._timestamp()}.log"
        return log_dir / filename

    @classmethod
    def _configure_formatter(cls) -> logging.Formatter:
        # Example: 2025-12-14 18:20:33 INFO my_func(123) Message text
        fmt = "%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s"
        datefmt = "%Y-%m-%d %H:%M:%S"
        # Use SafeFormatter by default (can be turned off via EEJO_LOG_SAFE_EXC=0)
        return SafeFormatter(fmt=fmt, datefmt=datefmt, safe_exc=cls._SAFE_EXC)

    @classmethod
    def _create_rotating_file_handler(cls, log_path: Path) -> RotatingFileHandler:
        handler = RotatingFileHandler(
            filename=str(log_path),
            mode="a",  # append to preserve earlier messages from same process run
            maxBytes=cls._MAX_BYTES,
            backupCount=cls._BACKUP_COUNT,
            encoding="utf-8",
            delay=False,
        )
        handler.setFormatter(cls._configure_formatter())
        handler.setLevel(cls._DEFAULT_LEVEL)
        return handler

    @classmethod
    def _create_console_handler(cls) -> Optional[logging.Handler]:
        if not cls._ENABLE_CONSOLE:
            return None
        ch = logging.StreamHandler()
        ch.setLevel(cls._DEFAULT_LEVEL)
        ch.setFormatter(cls._configure_formatter())
        return ch

    @classmethod
    def initialize(cls) -> logging.Logger:
        """Idempotent initialization—safe to call multiple times."""
        if cls._initialized:
            return cls.app_log

        # Optionally control internal logging package diagnostics
        logging.raiseExceptions = cls._RAISE_INTERNAL_LOGGING_EXCEPTIONS

        log_path = cls._build_log_path()
        logger = logging.getLogger(cls._DEFAULT_LOGGER_NAME)

        # Set base level on the logger (handlers can further filter)
        level = getattr(logging, cls._DEFAULT_LEVEL, logging.INFO)
        logger.setLevel(level)

        # Avoid duplicate handlers if reinitialized
        # Only add our handlers; leave any external handlers intact if already present.
        existing = {type(h) for h in logger.handlers}

        file_handler = cls._create_rotating_file_handler(log_path)
        if RotatingFileHandler not in existing:
            logger.addHandler(file_handler)

        console_handler = cls._create_console_handler()
        if console_handler and type(console_handler) not in existing:
            logger.addHandler(console_handler)

        cls.app_log = logger
        cls._initialized = True

        # Log basic context
        logger.info("Logger initialized: file=%s level=%s console=%s safe_exc=%s",str(log_path), cls._DEFAULT_LEVEL, cls._ENABLE_CONSOLE, str(log_path), cls._DEFAULT_LEVEL, cls._ENABLE_CONSOLE, cls._SAFE_EXC)
        return logger

Logger.initialize()
# Eager initialization to preserve original behavior,
# so `from Lib.LogerService import Logger; Logger.app_log.info("...")` works immediately.
