from abc import ABC


class StorageBase(ABC):
    """
    interface for Storage.
    """

    def __init__(self, **kwargs):
        pass

    def create_collection(self, **kwargs):
        """
        Create a collection.
        """
        raise NotImplementedError("Subclass should implement this method.")

    def list_collections(self, **kwargs):
        """
        List all collections.
        """
        raise NotImplementedError("Subclass should implement this method.")

    def get_collection_info(self, **kwargs):
        """
        Get collection information.
        """
        raise NotImplementedError("Subclass should implement this method.")

    def store(self, **kwargs):
        """
        Store data.
        """
        raise NotImplementedError("Subclass should implement this method.")

    def search(self, **kwargs):
        """
        Search relevant data.
        """
        raise NotImplementedError("Subclass should implement this method.")

    def hierarchical_search(self, **kwargs):
        """
        Hierarchical search relevant data.
        """
        raise NotImplementedError("Subclass should implement this method.")
