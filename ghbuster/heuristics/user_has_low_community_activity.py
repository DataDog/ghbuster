import logging
from datetime import datetime, timedelta, timezone

import github

from .base import MetadataHeuristic, HeuristicRunResult
from .. import TargetType, TargetSpec

logger = logging.getLogger(__name__)


class UserHasLowCommunityActivity(MetadataHeuristic):
    STARS_THRESHOLD = 1
    FOLLOWING_THRESHOLD = 1
    FOLLOWERS_THRESHOLD = 1
    ISSUES_OR_PR_THRESHOLD = 1
    ISSUES_OR_PR_TIME_PERIOD_DAYS = 30.5 * 6  # 6 months

    def id(self) -> str:
        return 'user.low_community_activity'

    def friendly_name(self) -> str:
        return "User with low community activity"

    def description(self) -> str:
        return "Detects when a user has very low community activity. This may indicate that the user is inauthentic."

    def target_type(self) -> TargetType:
        return TargetType.USER

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        user = github_client.get_user(login=target_spec.username)
        start_date = datetime.now(timezone.utc) - timedelta(days=self.ISSUES_OR_PR_TIME_PERIOD_DAYS)
        stars = user.get_starred()
        following = user.get_following()
        followers = user.get_followers()
        has_few_stars = stars.totalCount <= self.STARS_THRESHOLD
        has_few_following = following.totalCount <= self.FOLLOWING_THRESHOLD
        has_few_followers = followers.totalCount <= self.FOLLOWERS_THRESHOLD

        has_few_issues_or_prs = False
        issue_count = 0
        pr_count = 0
        try:
            issues = github_client.search_issues(
                f"type:issue author:{target_spec.username} created:>{start_date.strftime('%Y-%m-%d')}")
            prs = github_client.search_issues(
                f"type:pr author:{target_spec.username} created:>{start_date.strftime('%Y-%m-%d')}")

            issue_count = issues.totalCount
            pr_count = prs.totalCount
            has_few_issues_or_prs = issue_count + pr_count <= self.ISSUES_OR_PR_THRESHOLD

        except github.GithubException as e:
            if e.status == 422 and e.message == 'Validation Failed':
                logger.info("User %s has their profile activity in private mode, unable to list their PRs and issues", user.login)
            else:
                raise e

        logger.debug("User %s has %d stars, %d following, %d followers, %d issues, and %d PRs in the last %d days.",
                     target_spec.username, stars.totalCount, following.totalCount, followers.totalCount,
                     issue_count, pr_count, self.ISSUES_OR_PR_TIME_PERIOD_DAYS)

        if not has_few_stars or not has_few_following or not has_few_followers or not has_few_issues_or_prs:
            return HeuristicRunResult.PASSED()

        reason = 'User has low community activity: '
        triggered = []
        if has_few_stars:
            triggered.append(f"{stars.totalCount} stars (threshold: {self.STARS_THRESHOLD})")
        if has_few_following:
            triggered.append(f"{following.totalCount} following (threshold: {self.FOLLOWING_THRESHOLD})")
        if has_few_followers:
            triggered.append(f"{followers.totalCount} followers (threshold: {self.FOLLOWERS_THRESHOLD})")
        if has_few_issues_or_prs:
            triggered.append(
                f"{issues.totalCount + prs.totalCount} issues/PRs in the last {self.ISSUES_OR_PR_TIME_PERIOD_DAYS} days (threshold: {self.ISSUES_OR_PR_THRESHOLD})")

        reason += ', '.join(triggered)
        return HeuristicRunResult.TRIGGERED(additional_details=reason)
