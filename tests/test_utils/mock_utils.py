from unittest.mock import PropertyMock, MagicMock

class FakePaginatedList:
    def __init__(self, items):
        self._items = items
        self.totalCount = len(items)

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return FakePaginatedSlice(self._items[key])
        return self._items[key]


class FakePaginatedSlice:
    def __init__(self, items):
        self._items = items

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    @property
    def totalCount(self):
        raise AttributeError("'_Slice' object has no attribute 'totalCount'")


def mock_pygithub_list(items: list):
    return FakePaginatedList(items)