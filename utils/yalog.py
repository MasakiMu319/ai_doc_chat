import inspect
import logging
import sys
from typing import List, Dict

import pytz
from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class Log:
    logger_level = 0
    logger_file = True
    BEIJING_TZ = pytz.timezone("Asia/Shanghai")
    DEFAULT_CONFIG = [
        {
            "sink": sys.stdout,
            "level": logging.DEBUG,
            "format": "[<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>][<level>{level}</level>]"
            "[<yellow>{file}</yellow>:<cyan>{line}</cyan>]: <level>{message}</level>",
            "colorize": True,  # 自定义配色
            "serialize": False,  # 序列化数据打印
            "backtrace": True,  # 是否显示完整的异常堆栈跟踪
            "diagnose": True,  # 异常跟踪是否显示触发异常的方法或语句所使用的变量，生产环境应设为 False
            "enqueue": False,  # 默认线程安全。若想实现协程安全 或 进程安全，该参数设为 True
            "catch": True,  # 捕获异常
        }
    ]
    if logger_file:
        DEFAULT_CONFIG.append(
            {
                "sink": "logs/current.log",
                "level": logger_level,
                "format": "[{time:YYYY-MM-DD HH:mm:ss.SSS}][{level}][{file}:{line}]: {message}",
                "retention": "7 days",  # 日志保留时间
                "serialize": False,  # 序列化数据打印
                "backtrace": True,  # 是否显示完整的异常堆栈跟踪
                "diagnose": True,  # 异常跟踪是否显示触发异常的方法或语句所使用的变量，生产环境应设为 False
                "enqueue": False,  # 默认线程安全。若想实现协程安全 或 进程安全，该参数设为 True
                "catch": True,  # 捕获异常
            }
        )

    SERVERLESS_CONFIG = [
        {
            "sink": sys.stdout,
            "level": logger_level,
            "format": "[<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>][<level>{level}</level>]"
            "[<yellow>{file}</yellow>:<cyan>{line}</cyan>]: <level>{message}</level>",
            "colorize": False,  # 自定义配色
            "serialize": False,  # 序列化数据打印
            "backtrace": True,  # 是否显示完整的异常堆栈跟踪
            "diagnose": False,  # 异常跟踪是否显示触发异常的方法或语句所使用的变量，生产环境应设为 False
            "enqueue": False,  # 默认线程安全。若想实现协程安全 或 进程安全，该参数设为 True
            "catch": True,  # 捕获异常
        },
    ]

    @staticmethod
    def start(config: List[Dict] | None = None, mode: int = 0) -> None:
        if config:
            logger.configure(handlers=config)
        else:
            logger.configure(handlers=Log.DEFAULT_CONFIG)
        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
        logger.enable("__main__")

    @staticmethod
    def close() -> None:
        logger.disable("__main__")
