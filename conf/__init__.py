from pathlib import Path
import os
import logging
from dynaconf import Dynaconf
from utils.log import patch_logger

patch_logger(__name__, logging.DEBUG)

logger = logging.getLogger(__name__)

config_dir = Path(__file__).parent
ENV = os.environ.get("ENV", "dev")
if ENV == "prod":
    config_file = config_dir.joinpath("prod.toml")
else:
    config_file = config_dir.joinpath("dev.toml")

logger.info(f"Using config file: {config_file}")

settings = Dynaconf(
    envvar_prefix="AI_DOC_CHAT",
    settings_file=[config_file],
    load_dotenv=True,
)
