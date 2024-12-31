from logging import basicConfig, getLogger
import logfire


logfire.configure()


basicConfig(handlers=[logfire.LogfireLoggingHandler()])


logger = getLogger(__name__)
print(f"handlers: {len(logger.handlers)}")

logger.error(f"Hello {__name__}")
