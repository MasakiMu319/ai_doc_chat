from abc import ABC
from typing import List, Any


class BaseDataProcessor(ABC):
    """
    interface for Data Processor.
    """

    def process(self, **kwargs) -> List[Any]:
        return List[Any]
