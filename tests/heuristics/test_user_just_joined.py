import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, Mock

from github import NamedUser

from ghbuster import TargetSpec, TargetType
from ghbuster.heuristics.user_metadata_basic import UserJustJoinedHeuristic


class TestUserHasLowCommunityActivity(unittest.TestCase):
    def setUp(self):
        self.heuristic = UserJustJoinedHeuristic()

    @patch('ghbuster.heuristics.user_metadata_basic.github.Github')
    def test_positive(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="newuser")
        ghuser = Mock(NamedUser)
        ghuser.created_at = datetime.now(timezone.utc) - timedelta(days=UserJustJoinedHeuristic.THRESHOLD_DAYS - 1)
        gh.get_user.return_value = ghuser

        result = self.heuristic.run(gh, target_spec)
        self.assertTrue(result.triggered)

    @patch('ghbuster.heuristics.user_metadata_basic.github.Github')
    def test_negative(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="olduser")
        ghuser = Mock(NamedUser)
        ghuser.created_at = datetime.now(timezone.utc) - timedelta(days=UserJustJoinedHeuristic.THRESHOLD_DAYS + 1)
        gh.get_user.return_value = ghuser

        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)
