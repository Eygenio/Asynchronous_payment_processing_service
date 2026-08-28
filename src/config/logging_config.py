from uvicorn.logging import DefaultFormatter

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "color": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            "log_colors": {
                "DEBUG": "blue",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        },
        "uvicorn": {
            "()": DefaultFormatter,
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": True,
        },
    },
    "handlers": {
        "console_color": {
            "class": "logging.StreamHandler",
            "formatter": "color",
            "level": "INFO",
        },
        "uvicorn_console": {
            "class": "logging.StreamHandler",
            "formatter": "uvicorn",
            "level": "INFO",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["uvicorn_console"], "level": "INFO", "propagate": False},
        "uvicorn.access": {"handlers": ["uvicorn_console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"handlers": ["uvicorn_console"], "level": "INFO", "propagate": False},
        "src": {"handlers": ["console_color"], "level": "INFO", "propagate": False},
    },
}
