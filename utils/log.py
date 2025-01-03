import logging
import coloredlogs

logger = logging.getLogger(__name__)


def patch_logger(module: str, level: int):
    """
    Patch the logger for a specific module.

    :param module:
    :param level:
    :return:
    """
    patched_logger = logging.getLogger(module)
    patched_logger.setLevel(level=level)

    if not any(
        isinstance(handler, logging.StreamHandler)
        for handler in patched_logger.handlers
    ):
        coloredlogs.install(
            level=level,
            logger=patched_logger,
            fmt="%(asctime)s [%(name)s:%(lineno)d|%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level_styles={
                "debug": {"color": "blue"},
                "info": {"color": "green"},
                "warning": {"color": "yellow"},
                "error": {"color": "red"},
                "critical": {"color": "magenta"},
            },
            field_styles={
                "asctime": {"color": "white"},
                "filename": {"color": "cyan"},
                "lineno": {"color": "cyan"},
                "levelname": {"bold": True},
            },
        )
        logger.info(f"Module: {module} logger is patched.")

    patched_logger.propagate = False
