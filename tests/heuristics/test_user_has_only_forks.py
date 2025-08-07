import unittest
from unittest.mock import patch, Mock

from github import NamedUser

from ghbuster import TargetSpec, TargetType
from ghbuster.heuristics.user_has_only_forks import UserHasOnlyForkedRepos
from tests.test_utils.mock_utils import mock_pygithub_list


class TestUserHasOnlyForks(unittest.TestCase):
    def setUp(self):
        self.heuristic = UserHasOnlyForkedRepos()

    @patch('ghbuster.heuristics.user_has_only_forks.github.Github')
    def test_positive(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="foo")
        user = Mock(NamedUser)
        user.get_repos = Mock(return_value=mock_pygithub_list([
            Mock(fork=True, full_name="foo/repo1"),
            Mock(fork=True, full_name="foo/repo2")
        ]))
        gh.get_user.return_value = user

        result = self.heuristic.run(gh, target_spec)
        self.assertTrue(result.triggered)

    @patch('ghbuster.heuristics.user_has_only_forks.github.Github')
    def test_negative(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="foo")
        user = Mock(NamedUser)
        user.get_repos = Mock(return_value=mock_pygithub_list([
            Mock(fork=False, full_name="foo/repo1"),
            Mock(fork=True, full_name="foo/repo2")
        ]))
        gh.get_user.return_value = user

        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)

    @patch('ghbuster.heuristics.user_has_only_forks.github.Github')
    def test_negative_empty(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="foo")
        user = Mock(NamedUser)
        user.get_repos = Mock(return_value=mock_pygithub_list([]))
        gh.get_user.return_value = user

        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)
