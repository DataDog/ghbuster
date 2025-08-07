from github.NamedUser import NamedUser

from .user_has_forks_from_taken_down_repos import *
from .user_has_low_community_activity import *

logger = logging.getLogger(__name__)


# e.g. https://github.com/al1enb1t/cheatengine-for-linux
# or https://github.com/Caztemaz/Lnk-Exploit-FileBinder-Certificate-Spoofer-Reg-Doc-Cve-Rce in the case of taken down users
class RepoCommitsOnlyFromSuspiciousUnlinkedEmails(MetadataHeuristic):
    MAX_COMMITS = 100

    def id(self) -> str:
        return 'repo.commits_suspicious_unlinked_emails'

    def friendly_name(self) -> str:
        return "Repository commits only from suspicious unlinked emails"

    def description(self) -> str:
        return "Detects when a repository has commits with unlinked emails that also don't match the owner's username or full name."

    def target_type(self) -> TargetType:
        return TargetType.REPOSITORY

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        repo = github_client.get_repo(full_name_or_id=target_spec.repo_full_name())
        user = github_client.get_user(login=target_spec.username)
        normalized_username = user.login.lower()
        normalized_user_full_name = user.name.lower() if user.name else None
        commits = repo.get_commits()
        logger.debug("Analyzing %d commits for repository %s", commits.totalCount, target_spec.repo_full_name())
        num_suspicious = 0
        num_processed = 0
        unlinked_emails = set()
        for commit in commits:
            if num_processed == self.MAX_COMMITS:
                logger.debug("Reached max commit limit of %d, stopping the processing", self.MAX_COMMITS)
                break
            num_processed += 1
            normalized_committer_name = commit.commit.author.name.lower()
            name_matches = (normalized_committer_name in [normalized_username, normalized_user_full_name])
            if commit.author is None and not name_matches:
                # Case 1: the commit is not linked to any GitHub user based on the email
                # As it's a common misconfiguration, we only flag it if the author name in the git metadata doesn't match the user's username/name
                num_suspicious += 1
                unlinked_emails.add(commit.commit.author.email)
            elif commit.author is not None and self.commit_linked_to_taken_down_user(github_client, commit.author):
                # Case 2: the commit is linked to a GitHub user that has previously been taken down, we consider it "suspiciously-unlinked" too
                num_suspicious += 1
                unlinked_emails.add(commit.commit.author.email)

        if num_suspicious == num_processed:
            additional_details = f"The repository only has commits from unlinked emails ({', '.join(unlinked_emails)})."
            return HeuristicRunResult.TRIGGERED(additional_details=additional_details)

        return HeuristicRunResult.PASSED()

    @functools.cache
    def commit_linked_to_taken_down_user(self, github_client: github.Github, author: NamedUser) -> bool:
        # We know the commit is linked to a specific GitHub user, i.e. the git metadata email was linked to a specific user at the time of the commit
        # In some cases, the associated user doesn't exist anymore (e.g. taken down), so we consider the email as "currently unlinked" in this case
        # (like we'd see in the GitHub UI that the username is not clickable)
        try:
            github_client.get_user_by_id(author.id)
            return False  # no exception, the user exists
        except github.GithubException as e:
            if e.status == 404:
                return True
            raise e
