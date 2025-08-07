import unittest
from unittest.mock import patch, Mock

from github import NamedUser

from ghbuster import TargetSpec, TargetType
from ghbuster.heuristics.user_has_low_community_activity import UserHasLowCommunityActivity


class TestUserHasLowCommunityActivity(unittest.TestCase):
    def setUp(self):
        self.heuristic = UserHasLowCommunityActivity()

    @patch('ghbuster.heuristics.user_has_low_community_activity.github.Github')
    def test_positive(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="foo")
        user = Mock(NamedUser)
        user.login = target_spec.username
        user.get_starred = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.STARS_THRESHOLD - 1))
        user.get_following = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.FOLLOWING_THRESHOLD - 1))
        user.get_followers = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.FOLLOWERS_THRESHOLD - 1))
        gh.get_user.return_value = user
        gh.search_issues.return_value = Mock(totalCount=UserHasLowCommunityActivity.ISSUES_OR_PR_THRESHOLD - 1)
        result = self.heuristic.run(gh, target_spec)
        self.assertTrue(result.triggered)

    @patch('ghbuster.heuristics.user_has_low_community_activity.github.Github')
    def test_negative(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="foo")
        user = Mock(NamedUser)
        user.login = target_spec.username
        user.get_starred = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.STARS_THRESHOLD + 1))
        user.get_following = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.FOLLOWING_THRESHOLD + 1))
        user.get_followers = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.FOLLOWERS_THRESHOLD + 1))
        gh.get_user.return_value = user
        gh.search_issues.return_value = Mock(totalCount=UserHasLowCommunityActivity.ISSUES_OR_PR_THRESHOLD + 1)
        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)

    @patch('ghbuster.heuristics.user_has_low_community_activity.github.Github')
    def test_negative_single_attribute_ok(self, gh):
        target_spec = TargetSpec(target_type=TargetType.USER, username="foo")
        user = Mock(NamedUser)
        user.login = target_spec.username
        user.get_starred = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.STARS_THRESHOLD + 1))
        user.get_following = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.FOLLOWING_THRESHOLD - 1))
        user.get_followers = Mock(return_value=Mock(totalCount=UserHasLowCommunityActivity.FOLLOWERS_THRESHOLD - 1))
        gh.get_user.return_value = user
        gh.search_issues.return_value = Mock(totalCount=UserHasLowCommunityActivity.ISSUES_OR_PR_THRESHOLD - 1)
        result = self.heuristic.run(gh, target_spec)
        self.assertFalse(result.triggered)
