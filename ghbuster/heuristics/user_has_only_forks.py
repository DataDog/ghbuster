import logging

import github

from .base import MetadataHeuristic, HeuristicRunResult
from .. import TargetType, TargetSpec

logger = logging.getLogger(__name__)


# e.g. https://github.com/sweetboy235
class UserHasOnlyForkedRepos(MetadataHeuristic):
    def id(self) -> str:
        return 'user.repos_only_forks'

    def friendly_name(self) -> str:
        return "User has only forks"

    def description(self) -> str:
        return "Detects all of a user's repositories are forks. This may be an indication that the user is used solely to make other repositories appear legitimate."

    def target_type(self) -> TargetType:
        return TargetType.USER

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        user = github_client.get_user(login=target_spec.username)
        user_repos = user.get_repos(type='owner')
        has_only_forks = user_repos.totalCount > 0 and not any(not repo.fork for repo in user_repos)

        if has_only_forks:
            additional_details = f"The user {target_spec.username} has only forked repositories."
            return HeuristicRunResult.TRIGGERED(additional_details=additional_details)

        return HeuristicRunResult.PASSED()
