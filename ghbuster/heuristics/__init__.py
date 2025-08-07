from .repo_commits_only_from_suspicious_unlinked_emails import *
from .repo_has_stargazzers_who_joined_the_same_day import *
from .repo_starred_by_suspicious_users import *
from .user_has_only_commits_from_unlinked_emails import *
from .user_has_only_forks import *
from .user_looks_legit import UserLooksLegit

ALL_HEURISTICS = {
    UserJustJoinedHeuristic(),
    UserMissingCommonFields(),
    UserHasOnlyCommitsFromUnlinkedEmails(),  # can be a bit slow as it analyzes all commits from the user's repositories
    UserHasLowCommunityActivity(),
    RepoStarredBySuspiciousUsers(),
    RepoCommitsOnlyFromSuspiciousUnlinkedEmails(),
    UserHasForksFromTakenDownRepos(),
    UserHasOnlyForkedRepos(),
    RepoHasStargazersWhoJoinedOnTheSameDay()
}
