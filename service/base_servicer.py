from abc import ABC, abstractmethod


class BaseServicer(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def prepare_data(self):
        pass

    @abstractmethod
    def search_relevant_contents(self):
        pass

    @abstractmethod
    def chat(self):
        pass
