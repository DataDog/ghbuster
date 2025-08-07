import unittest
from unittest.mock import patch, Mock

from github import Repository, GithubException

from ghbuster import TargetSpec, TargetType
from ghbuster.heuristics.user_has_forks_from_taken_down_repos import UserHasForksFromTakenDownRepos
from tests.test_utils.mock_utils import mock_pygithub_list


class TestUserHasForksFromTakenDownRepos(unittest.TestCase):
    def setUp(self):
        self.heuristic = UserHasForksFromTakenDownRepos()

    @patch('ghbuster.heuristics.user_has_forks_from_taken_down_repos.github.Github')
    def test_positive(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="fork")

        parent_repo1 = Mock(Repository, full_name='foo/repo1')
        repo1 = Mock(spec=Repository, fork=True, full_name="fork/repo1")
        repo1.parent = parent_repo1

        parent_repo2 = Mock(Repository, full_name='foo/repo2')  # not existing anymore
        repo2 = Mock(spec=Repository, fork=True, full_name="fork/repo2")
        repo2.parent = parent_repo2
        user_repos = [repo1, repo2]

        other_repos = [
            parent_repo1
            # note: parent_repo2 is not included here, simulating that it has been taken down
        ]

        def side_effect(repo_name):
            user_repos_by_name = {repo.full_name: repo for repo in user_repos}
            other_repos_by_name = {repo.full_name: repo for repo in other_repos}
            if repo_name in user_repos_by_name:
                return user_repos_by_name[repo_name]
            elif repo_name in other_repos_by_name:
                return other_repos_by_name[repo_name]
            else:
                raise GithubException(status=404)

        gh.get_repo.side_effect = side_effect
        gh.get_user.return_value.get_repos = Mock(return_value=mock_pygithub_list(user_repos))
        result = self.heuristic.run(gh, target_spec)
        self.assertTrue(result.triggered)

    @patch('ghbuster.heuristics.user_has_forks_from_taken_down_repos.github.Github')
    def test_negative_no_repo(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="fork")
        gh.get_user.return_value.get_repos = Mock(return_value=mock_pygithub_list([]))
        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)

    @patch('ghbuster.heuristics.user_has_forks_from_taken_down_repos.github.Github')
    def test_negative_forks_with_existing_parents(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="fork")

        parent_repo1 = Mock(Repository, full_name='foo/repo1')
        repo1 = Mock(spec=Repository, fork=True, full_name="fork/repo1")
        repo1.parent = parent_repo1

        parent_repo2 = Mock(Repository, full_name='foo/repo2')  # not existing anymore
        repo2 = Mock(spec=Repository, fork=True, full_name="fork/repo2")
        repo2.parent = parent_repo2
        user_repos = [repo1, repo2]

        other_repos = [
            parent_repo1,
            parent_repo2
        ]
        user_repos_by_name = {repo.full_name: repo for repo in user_repos}
        other_repos_by_name = {repo.full_name: repo for repo in other_repos}

        gh.get_repo.side_effect = lambda repo_name: user_repos_by_name[
            repo_name] if repo_name in user_repos_by_name else other_repos_by_name[repo_name]
        gh.get_user.return_value.get_repos = Mock(return_value=mock_pygithub_list(user_repos))
        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)

    @patch('ghbuster.heuristics.user_has_forks_from_taken_down_repos.github.Github')
    def test_negative_no_forks(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="fork")

        user_repos = [
            Mock(spec=Repository, fork=False, full_name="foo/repo1"),
            Mock(spec=Repository, fork=False, full_name="foo/repo2")
        ]

        gh.get_repo.return_value = Mock(return_value=mock_pygithub_list(user_repos))
        gh.get_user.return_value.get_repos = Mock(return_value=mock_pygithub_list(user_repos))
        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)
