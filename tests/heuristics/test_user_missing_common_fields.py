import unittest
from unittest.mock import patch, MagicMock

from github import NamedUser

from ghbuster import TargetSpec, TargetType
from ghbuster.heuristics.user_metadata_basic import UserMissingCommonFields


class TestUserHasLowCommunityActivity(unittest.TestCase):
    def setUp(self):
        self.heuristic = UserMissingCommonFields()

    @patch('ghbuster.heuristics.user_metadata_basic.github.Github')
    def test_positive(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="user")
        ghuser = MagicMock(NamedUser)
        ghuser.bio = None
        ghuser.company = None
        ghuser.location = None
        ghuser.name = None
        gh.get_user.return_value = ghuser

        result = self.heuristic.run(gh, target_spec)
        self.assertTrue(result.triggered)

    @patch('ghbuster.heuristics.user_metadata_basic.github.Github')
    def test_negative(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="user")
        ghuser = MagicMock(NamedUser)
        ghuser.bio = None
        ghuser.company = None
        ghuser.location = None
        ghuser.name = 'John Doe'
        gh.get_user.return_value = ghuser
        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)

