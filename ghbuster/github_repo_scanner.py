import logging

import github

from . import TargetType, TargetSpec
from .heuristics import HeuristicRunResult, MetadataHeuristic

logger = logging.getLogger(__name__)


class GitHubScanner:
    def __init__(self, target_spec: TargetSpec, github_client: github.Github, heuristics: list[MetadataHeuristic]):
        self.target_spec = target_spec
        self.github_client = github_client
        self.heuristics = heuristics

    def ensure_authenticated(self):
        try:
            current_user = self.github_client.get_user()
            print(f"Authenticated as {current_user.login}")
        except github.GithubException as e:
            raise ValueError(f"Authentication failed. Please check your GitHub token (status code {e.status})")

    def validate_target_spec(self):
        if self.target_spec.target_type == TargetType.REPOSITORY:
            try:
                self.github_client.get_repo(f"{self.target_spec.username}/{self.target_spec.repo_name}")
                return  # all good
            except github.GithubException as e:
                raise ValueError(
                    f"Invalid repository '{self.target_spec.username}/{self.target_spec.repo_name}': {e.data['message']}")
        elif self.target_spec.target_type == TargetType.USER:
            try:
                self.github_client.get_user(self.target_spec.username)
                return  # all good
            except github.GithubException as e:
                raise ValueError(f"Invalid user '{self.target_spec.username}': {e.data['message']}")
        else:
            raise ValueError("Unsupported target type")

    def scan(self) -> list[HeuristicRunResult]:
        results = []
        for heuristic in self.heuristics:
            if heuristic.target_type() != self.target_spec.target_type:
                continue

            logger.debug("Running heuristic %s on %s", heuristic.id(), self.target_spec)
            result = heuristic.run(self.github_client, self.target_spec)
            result.heuristic = heuristic
            results.append(result)
        return results
