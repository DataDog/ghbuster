from unittest.mock import MagicMock


def mock_pygithub_list(items: list) -> MagicMock:
    mock_list = MagicMock()
    mock_list.__iter__.return_value = iter(items)
    mock_list.__len__.return_value = len(items)
    mock_list.totalCount = len(items)
    return mock_list
