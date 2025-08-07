import logging
from datetime import timezone, datetime

import github

from .base import MetadataHeuristic, HeuristicRunResult
from .. import TargetType, TargetSpec

logger = logging.getLogger(__name__)

"""
UserLooksLegit is used as a strong signal that a user is authentic, to avoid running extraneous heuristics on them.
"""


class UserLooksLegit(MetadataHeuristic):
    def id(self) -> str:
        return 'user.looks_legit'

    def friendly_name(self) -> str:
        return "User is likely legitimate"

    def description(self) -> str:
        return "The user is likely legitimate."

    def target_type(self) -> TargetType:
        return TargetType.USER

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        user = github_client.get_user(login=target_spec.username)

        joined_days_ago = (datetime.now(timezone.utc) - user.created_at).days
        likely_legit = (
                user.public_repos > 10 and
                joined_days_ago > 365 and
                user.followers > 10 and
                user.following > 10 and
                user.name is not None and
                (user.company is not None or user.location is not None or user.bio is not None) and
                user.public_repos > 5
        )
        additional_details = (
            "\n"
            f"- The user has {user.public_repos} public repos\n"
            f"- The user has {user.followers} followers, and is following {user.following} users.\n"
            f"- The user joined {joined_days_ago} days ago.\n"
            f"- The user has a name set on their profile ({user.name})\n"
            f"- The user has the usual fields set on their profile.\n"
        )
        if likely_legit:
            return HeuristicRunResult.TRIGGERED(additional_details=additional_details)
        else:
            return HeuristicRunResult.SKIPPED()
