import functools
import logging

import github

from .base import MetadataHeuristic, HeuristicRunResult
from .. import TargetType, TargetSpec

logger = logging.getLogger(__name__)


# e.g. https://github.com/mrrebrik3765
class UserHasForksFromTakenDownRepos(MetadataHeuristic):

    def __init__(self, max_forks_to_analyze: int = 10):
        super().__init__()
        self.max_forks_to_analyze = max_forks_to_analyze

    def id(self) -> str:
        return 'user.forks_from_taken_down_repos'

    def friendly_name(self) -> str:
        return "User has forks of taken-down repositories"

    def description(self) -> str:
        return "Detects when a user has forks from repositories that have been taken down. This may indicate that the user is being leveraged as part of a campaign to make inauthentic repositories appear legitimate."

    def target_type(self) -> TargetType:
        return TargetType.USER

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        user = github_client.get_user(login=target_spec.username)
        user_repos = user.get_repos(type='owner')
        taken_down_repos = set()
        num_forks_analyzed = 0
        for repo in user_repos:
            if repo.fork:
                if num_forks_analyzed >= self.max_forks_to_analyze:
                    logger.debug("Reached maximum number of forks to analyze (%d), stopping further checks",
                                 self.max_forks_to_analyze)
                    break
                num_forks_analyzed += 1
                logger.debug("Analyzing forked repository %s owned by user %s", repo.full_name, target_spec.username)
                try:
                    original_name = repo.parent.full_name
                    if not self.repo_exists(github_client, original_name):
                        taken_down_repos.add(original_name)
                except github.GithubException as e:
                    if e.status in [403, 451] and e.message == 'Repository access blocked':
                        # tos violation, i.e. soft takedown
                        # TODO should probably be taken into account by the heuristic
                        logger.warning("Repository %s owned by user %s is blocked, ignoring", repo.full_name,
                                       target_spec.username)
                    else:
                        raise e

        if len(taken_down_repos) > 0:
            additional_details = f"The user {target_spec.username} has forks from taken down repositories: {', '.join(taken_down_repos)}."
            return HeuristicRunResult.TRIGGERED(additional_details=additional_details)

        return HeuristicRunResult.PASSED()

    @functools.cache
    def repo_exists(self, github_client: github.Github, full_name: str) -> bool:
        try:
            github_client.get_repo(full_name)
            return True
        except github.GithubException as e:
            if e.status == 404:
                return False
            elif e.status in [403, 451] and e.message == 'Repository access blocked':
                # tos violation or other access issues
                return False
            raise
