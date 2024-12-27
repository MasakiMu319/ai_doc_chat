from abc import ABC, abstractmethod


class StorageBase(ABC):
    """
    interface for Storage.
    """

    @abstractmethod
    def __init__(self, **kwargs):
        pass

    @abstractmethod
    def create_collection(self, **kwargs):
        """
        Create a collection.
        """
        raise NotImplementedError("Subclass should implement this method.")

    @abstractmethod
    def list_collections(self, **kwargs):
        """
        List all collections.
        """
        raise NotImplementedError("Subclass should implement this method.")

    @abstractmethod
    def get_collection_info(self, **kwargs):
        """
        Get collection information.
        """
        raise NotImplementedError("Subclass should implement this method.")

    @abstractmethod
    def store(self, **kwargs):
        """
        Store data.
        """
        raise NotImplementedError("Subclass should implement this method.")

    @abstractmethod
    def search(self, **kwargs):
        """
        Search relevant data.
        """
        raise NotImplementedError("Subclass should implement this method.")

    @abstractmethod
    def hierarchical_search(self, **kwargs):
        """
        Hierarchical search relevant data.
        """
        raise NotImplementedError("Subclass should implement this method.")
