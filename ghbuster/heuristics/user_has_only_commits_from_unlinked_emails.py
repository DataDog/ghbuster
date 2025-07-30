import logging

import github

from .base import MetadataHeuristic, HeuristicRunResult
from .. import TargetType, TargetSpec
from ..service.emails_extractor import GitHubCommitEmailExtractor

logger = logging.getLogger(__name__)


class UserHasOnlyCommitsFromUnlinkedEmails(MetadataHeuristic):
    def id(self) -> str:
        return 'user.commits_unlinked_emails'

    def friendly_name(self) -> str:
        return "User has only commits from unlinked emails"

    def description(self) -> str:
        return "Detects when all of a user's commits are from emails not linked to their GitHub profiles. This may indicate a threat actor leveraging distinct inauthentic accounts."

    def target_type(self) -> TargetType:
        return TargetType.USER

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        extractor = GitHubCommitEmailExtractor(github_client, target_spec, include_forks=False,
                                               include_unlinked_emails=True,
                                               include_emails_linked_to_other_users=False)
        emails = extractor.find_emails()
        has_linked_emails = any(email.is_linked_to_user for email in emails)
        if has_linked_emails:
            return HeuristicRunResult.PASSED()
        else:
            email_addresses = list[str]()
            for e in emails:
                email_addresses.append(e.email)

            return HeuristicRunResult.TRIGGERED(
                f"The user {target_spec.username} has only commits from unlinked emails: '{', '.join(email_addresses)}'.")
