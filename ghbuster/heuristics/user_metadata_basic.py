import datetime
from datetime import datetime, timezone

import github

from .base import MetadataHeuristic, HeuristicRunResult
from .. import TargetType, TargetSpec


class BasicUserMetadataHeuristic(MetadataHeuristic):
    pass


class UserJustJoinedHeuristic(MetadataHeuristic):
    THRESHOLD_DAYS = 7

    def id(self) -> str:
        return 'user.just_joined'

    def friendly_name(self) -> str:
        return "User recently joined GitHub"

    def description(self) -> str:
        return f"The GitHub user joined the platform less than {self.THRESHOLD_DAYS} days ago."

    def target_type(self) -> TargetType:
        return TargetType.USER

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        user = github_client.get_user(login=target_spec.username)
        if user.created_at is None:
            return HeuristicRunResult.PASSED()

        days_since_creation = (datetime.now(timezone.utc) - user.created_at).days
        if days_since_creation >= self.THRESHOLD_DAYS:
            return HeuristicRunResult.PASSED()
        else:
            additional_details = f"User {target_spec.username} joined GitHub on {user.created_at.strftime('%Y-%m-%d')} ({days_since_creation} days ago)."
            return HeuristicRunResult.TRIGGERED(additional_details=additional_details)


class UserMissingCommonFields(MetadataHeuristic):
    FIELDS = [
        'name',
        'company',
        'bio',
        'location'
    ]

    def id(self) -> str:
        return 'user.missing_common_fields'

    def friendly_name(self) -> str:
        return "User has none of the common profile fields set"

    def description(self) -> str:
        return f"Detects when a GitHub is missing a number of highly-common fields ({', '.join(self.FIELDS)}) in their profile."

    def target_type(self) -> TargetType:
        return TargetType.USER

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        user = github_client.get_user(login=target_spec.username)
        if all(getattr(user, field) is None for field in self.FIELDS):
            additional_details = f"User {target_spec.username} has none of the common fields ({', '.join(self.FIELDS)}) set."
            return HeuristicRunResult.TRIGGERED(additional_details=additional_details)

        return HeuristicRunResult.PASSED()
