from github.NamedUser import NamedUser

from .user_has_forks_from_taken_down_repos import *
from .user_has_low_community_activity import *
from .user_has_only_forks import *
from .user_looks_legit import UserLooksLegit
from .user_metadata_basic import *

logger = logging.getLogger(__name__)


class RepoStarredBySuspiciousUsers(MetadataHeuristic):
    PERCENT_THRESHOLD = 80
    MAX_STARGAZERS = 101

    def id(self) -> str:
        return 'repo.starred_by_suspicious_users'

    def friendly_name(self) -> str:
        return "Repository starred by suspicious users"

    def description(self) -> str:
        return f"Detects when a repository has over {round(self.PERCENT_THRESHOLD*100)} % of stars from suspicious users matching heuristics they may be inauthentic."

    def target_type(self) -> TargetType:
        return TargetType.REPOSITORY

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        # Here we want heuristics that are quick to run
        repo = github_client.get_repo(full_name_or_id=target_spec.repo_full_name())
        all_stargazers = repo.get_stargazers()
        stargazer_count = all_stargazers.totalCount

        if stargazer_count == 0:
            logger.debug("Repository %s has no stargazers.", target_spec.repo_full_name())
            return HeuristicRunResult.PASSED()
        elif stargazer_count > self.MAX_STARGAZERS:
            logger.info("Repository %s has too many stargazers (%d) to analyze, ignoring it.",
                         target_spec.repo_full_name(), all_stargazers.totalCount)
            return HeuristicRunResult.PASSED()

        logger.info("Analyzing %d stargazers for repository %s", stargazer_count,
                     target_spec.repo_full_name())
        suspicious_stargazers = {}  # mapping from username to the list of triggered heuristics for this user
        for stargazer in all_stargazers:
            user = github_client.get_user(login=stargazer.login)
            if UserLooksLegit().run(github_client, target_spec).triggered:
                logger.info("The user %s exhibits strong characteristics of a legitimate user, skipping", user.login)
                continue

            user_heuristics = self.get_heuristics_to_run_for_user(user)
            logger.info("Analyzing if stargazer %s looks suspicious by running %d heuristics", user.login, len(user_heuristics))
            for heuristic in user_heuristics:
                result = heuristic.run(github_client, TargetSpec(TargetType.USER, username=user.login))
                if result.triggered:
                    logger.debug("Stargazer %s triggered heuristic %s", user.login, heuristic.id())
                    if user.login not in suspicious_stargazers:
                        suspicious_stargazers[user.login] = []
                    suspicious_stargazers[user.login].append(heuristic.id())

        ratio = 100 * len(suspicious_stargazers) / stargazer_count if stargazer_count > 0 else 0
        if ratio >= self.PERCENT_THRESHOLD:
            additional_details = f"The repository has {len(suspicious_stargazers)} stargazers ({round(ratio)} %) that triggered suspicious user heuristics: {', '.join(suspicious_stargazers.keys())}."
            return HeuristicRunResult.TRIGGERED(additional_details=additional_details)

        return HeuristicRunResult.PASSED()

    @staticmethod
    def get_heuristics_to_run_for_user(user: NamedUser) -> set[MetadataHeuristic]:
        heuristics: set[MetadataHeuristic] = {
            UserJustJoinedHeuristic(),
            UserMissingCommonFields(),
            UserHasLowCommunityActivity(),
            UserHasOnlyForkedRepos()
        }

        if user.followers <= 100:
            # since this heuristic can take time, we only run it for users that have a higher chance of being inauthentic
            heuristics.add(UserHasForksFromTakenDownRepos(max_forks_to_analyze=20))

        return heuristics

