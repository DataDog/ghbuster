import functools
import logging

import github
from github.Repository import Repository
from github.Commit import Commit
from github.NamedUser import NamedUser

from .. import TargetSpec, TargetType

logger = logging.getLogger(__name__)


class EmailResult:
    email: str
    is_linked_to_user: bool

    def __init__(self, email: str, is_linked_to_user: bool):
        self.email = email
        self.is_linked_to_user = is_linked_to_user

    def __eq__(self, other):
        if not isinstance(other, EmailResult):
            return False
        return self.email == other.email

    def __hash__(self):
        return hash(self.email)


class GitHubCommitEmailExtractor:
    def __init__(self, github_client: github.Github, target_spec: TargetSpec, include_forks: bool = False,
                 include_emails_linked_to_other_users: bool = False, include_unlinked_emails: bool = True, max_commits_to_analyze_per_repo: int = 100):
        self.github_client = github_client
        self.target_spec = target_spec
        self.include_forks = include_forks
        self.include_emails_linked_to_other_users = include_emails_linked_to_other_users
        self.include_unlinked_emails = include_unlinked_emails
        self.max_commits_to_analyze_per_repo = max_commits_to_analyze_per_repo

    def find_emails(self) -> set[EmailResult]:
        emails = set[EmailResult]()

        if self.target_spec.target_type == TargetType.REPOSITORY:
            repo = self.github_client.get_repo(self.target_spec.repo_full_name())
            emails = self._find_emails_from_repository(repo)
        elif self.target_spec.target_type == TargetType.USER:
            user = self.github_client.get_user(self.target_spec.username)
            repos = user.get_repos(type='owner')
            logger.debug("Found %d GitHub repositories for user %s", repos.totalCount, self.target_spec.username)
            for repo in repos:
                if repo.fork and not self.include_forks:
                    logger.debug("Skipping forked repository %s", repo.full_name)
                    continue
                repo_emails = self._find_emails_from_repository(repo)
                emails.update(repo_emails)

        return emails

    def _find_emails_from_repository(self, repository: github.Repository) -> set[EmailResult]:
        logger.debug("Identifying emails from repository %s", repository.full_name)
        emails = set[EmailResult]()
        branches = repository.get_branches()
        logger.debug("Found %d branches in repository %s", branches.totalCount, repository.full_name)
        num_commits_processed = 0
        for branch in branches:
            commits = repository.get_commits(sha=branch.name)
            logger.debug("Processing branch '%s' with %d commits", branch.name, commits.totalCount)
            for commit in commits:
                if num_commits_processed > self.max_commits_to_analyze_per_repo:
                    logger.debug("Reached max processing limit of %d commits per repo for %s, going to the next one",
                                 self.max_commits_to_analyze_per_repo, repository.full_name)
                    return emails
                num_commits_processed += 1
                is_commit_linked_to_user: bool
                if commit.author is None or self.commit_linked_to_taken_down_user(commit.author):
                    is_commit_linked_to_user = False
                    if not self.include_unlinked_emails:
                        logger.debug("Skipping commit %s (no Git authorship information)", commit.sha[:6])
                        continue
                else:
                    is_commit_linked_to_user = True
                    if not self.is_commit_by_current_user(commit) and not self.include_emails_linked_to_other_users:
                        logger.debug("Skipping commit %s by Git author %s (linked to another user %s)", commit.sha[:6],
                                     commit.commit.author.email, commit.author.login)
                        continue

                emails.add(
                    EmailResult(email=commit.commit.author.email.lower(), is_linked_to_user=is_commit_linked_to_user))

        return emails

    def is_commit_by_current_user(self, commit: Commit) -> bool:
        # Note: we need to compare author user ID and not only usernames, because sometimes users get renamed
        current_user = self.github_client.get_user(self.target_spec.username)
        return commit.author.id == current_user.id

    @functools.cache
    def commit_linked_to_taken_down_user(self, author: NamedUser) -> bool:
        # We know the commit is linked to a specific GitHub user, i.e. the git metadata email was linked to a specific user at the time of the commit
        # In some cases, the associated user doesn't exist anymore (e.g. taken down), so we consider the email as "currently unlinked" in this case
        # (like we'd see in the GitHub UI that the username is not clickable)
        try:
            self.github_client.get_user_by_id(author.id)
            return False # no exception, the user exists
        except github.GithubException as e:
            if e.status == 404:
                return True
            raise e


"""
    NOTE: The version below doesn't work because the GitHub API doesn't support searching with user:x directly, or it returns "The search contains only logical operators (AND / OR / NOT) without any search terms", most likely to protect against abuse.
    
    def find_emails(self) -> set[str]:
        emails = set()
        search_query = ""
        if self.target_spec.target_type == TargetType.REPOSITORY:
            search_query = f'repo:{self.target_spec.repo_full_name()}'
        elif self.target_spec.target_type == TargetType.USER:
            search_query = f'user:{self.target_spec.username}'

        commits = self.github_client.search_commits(search_query)
        print("Search got back {} commits".format(commits.totalCount))
        for commit in commits:
            print(commit.sha)
            # If we only want "linked emails", we keep only commits where the committer's email has been linked to the user profile
            if self.only_linked_emails and (
                    commit.author is None or commit.author.login is None or commit.author.login != self.target_spec.username):
                continue
            else:
                email = commit.commit.author.email.lower()
                if email not in emails:
                    emails.add(email)
        return emails
"""
