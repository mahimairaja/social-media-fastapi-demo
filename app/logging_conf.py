from logging.config import dictConfig

from app.config import DevConfig, config


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "%(asctime)s:%(msecs)03dz | %(levelname)-8s | %(name)s:%(lineno)s - %(message)s",
                },
                # 03d 3 digit
                # z iso format
                # -8s always 8 characters long
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filename": "storeapi.log",
                    "maxBytes": 1024 * 1025 * 2,  # 2 megabytes
                    "backupCount": 5,
                    "encoding": "utf8",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
                "app": {  # root.storeapi.routers.post
                    "handlers": ["default", "rotating_file"],
                    "level": "DEBUG" if isinstance(config, DevConfig) else "INFO",
                    "propagate": False,
                },
                "databases": {"handlers": ["default"], "level": "WARNING"},
                "aiosqlite": {"handlers": ["default"], "level": "WARNING"},
            },
        }
    )
