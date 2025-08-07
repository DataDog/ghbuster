import dataclasses
import datetime
import logging
from typing import Iterable

import requests

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class GitHubEvent:
    event_type: str
    actor_login: str
    repo_name: str
    created_at: datetime
    _raw: dict[str, str]

    def from_dict(self, data: dict[str, str]) -> 'GitHubEvent':
        self.event_type = data.get('event_type', '')
        self.actor_login = data.get('actor_login', '')
        self.repo_name = data.get('repo_name', '')
        self.created_at = datetime.datetime.fromisoformat(data.get('created_at', ''))
        self._raw = data
        return self


class GitHubArchive:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers['User-Agent'] = 'ghbuster'

    def query(self, query: str) -> Iterable[GitHubEvent]:
        url = "https://play.clickhouse.com/"
        url_params = {
            'user': 'explorer',
            'default_format': 'JSONStrings',
        }
        response = self.session.post(url, params=url_params, data=query)
        response.raise_for_status()
        data = response.json().get('data', [])
        logger.debug("Query executed successfully, received %d rows", len(data))
        result = []
        for row in data:
            result.append(GitHubEvent(
                event_type=row.get('event_type', None),
                actor_login=row.get('actor_login', None),
                repo_name=row.get('repo_name', None),
                created_at=datetime.datetime.fromisoformat(row.get('created_at', '')),
                _raw=row
            ))

        return result
