import unittest
from datetime import datetime
from unittest.mock import patch, Mock

from github import Repository

from ghbuster import TargetSpec, TargetType
from ghbuster.heuristics.repo_has_stargazzers_who_joined_the_same_day import RepoHasStargazersWhoJoinedOnTheSameDay
from tests.test_utils.date_utils import random_date
from tests.test_utils.mock_utils import mock_pygithub_list


class TestUserHasLowCommunityActivity(unittest.TestCase):
    def setUp(self):
        self.heuristic = RepoHasStargazersWhoJoinedOnTheSameDay()

    @patch('ghbuster.heuristics.repo_has_stargazzers_who_joined_the_same_day.github.Github')
    def test_positive_all_stargazers_joined_same_day(self, gh):
        target_spec = TargetSpec(target_type=TargetType.REPOSITORY, username="user", repo_name="repo")
        ghrepo = Mock(Repository)
        ghrepo.get_stargazers = Mock(return_value=mock_pygithub_list([
            Mock(login="user1", created_at=datetime.strptime("2025-08-07T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")),
            Mock(login="user2", created_at=datetime.strptime("2025-08-07T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")),
            Mock(login="user3", created_at=datetime.strptime("2025-08-07T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ")),
            Mock(login="user4", created_at=datetime.strptime("2025-08-07T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"))
        ]))
        gh.get_repo.return_value = ghrepo

        result = self.heuristic.run(gh, target_spec)
        self.assertTrue(result.triggered)

    @patch('ghbuster.heuristics.repo_has_stargazzers_who_joined_the_same_day.github.Github')
    def test_positive_threshold_of_stargazers_joined_same_day(self, gh):
        target_spec = TargetSpec(target_type=TargetType.REPOSITORY, username="user", repo_name="repo")
        ghrepo = Mock(Repository)
        num_users = 10
        num_joined_same_day = round(RepoHasStargazersWhoJoinedOnTheSameDay.THRESHOLD_PERCENT / 100 * num_users) + 2
        same_day_users = [
            Mock(login=f"user{i}", created_at=datetime.strptime("2025-08-07T00:00:00Z", "%Y-%m-%dT%H:%M:%SZ"))
            for i in range(num_joined_same_day)
        ]
        other_users = [
            Mock(login=f"user{i}", created_at=random_date())
            for i in range(num_users - num_joined_same_day)
        ]
        ghrepo.get_stargazers = Mock(return_value=mock_pygithub_list(same_day_users + other_users))
        gh.get_repo.return_value = ghrepo

        result = self.heuristic.run(gh, target_spec)
        self.assertTrue(result.triggered)

    @patch('ghbuster.heuristics.repo_has_stargazzers_who_joined_the_same_day.github.Github')
    def test_negative_not_enough_stargazers(self, gh):
        target_spec = TargetSpec(target_type=TargetType.REPOSITORY, username="user", repo_name="repo")
        ghrepo = Mock(Repository)
        ghrepo.get_stargazers = Mock(return_value=mock_pygithub_list([]))
        gh.get_repo.return_value = ghrepo

        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)

    @patch('ghbuster.heuristics.repo_has_stargazzers_who_joined_the_same_day.github.Github')
    def test_negative_too_many_stargazers(self, gh):
        target_spec = TargetSpec(target_type=TargetType.REPOSITORY, username="user", repo_name="repo")
        ghrepo = Mock(Repository)
        stargazers = [
            Mock(login=f"user{i}", created_at=random_date())
            for i in range(RepoHasStargazersWhoJoinedOnTheSameDay.MAX_STARGAZERS + 1)
        ]
        ghrepo.get_stargazers = Mock(return_value=mock_pygithub_list(stargazers))
        gh.get_repo.return_value = ghrepo

        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)
