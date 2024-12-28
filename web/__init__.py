import logging
from utils.log import patch_logger

patch_logger(module=__name__, level=logging.DEBUG)
