from .user_has_low_community_activity import *

logger = logging.getLogger(__name__)


# e.g. https://github.com/heidarodeer/crypto-clipper/stargazers
class RepoHasStargazersWhoJoinedOnTheSameDay(MetadataHeuristic):
    THRESHOLD_PERCENT = 50
    MIN_STARGAZERS = 2
    MAX_STARGAZERS = 100

    def id(self) -> str:
        return 'repo.stargazers_joined_same_day'

    def friendly_name(self) -> str:
        return "Repository has stargazers who joined the same day"

    def description(self) -> str:
        return "Detects when a repository has a large proportion of its stargazers who joined GitHub on the same day, which may indicate a coordinated effort to boost the repository's popularity."

    def target_type(self) -> TargetType:
        return TargetType.REPOSITORY

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        repo = github_client.get_repo(full_name_or_id=target_spec.repo_full_name())
        all_stargazers = repo.get_stargazers()
        num_stargazers = all_stargazers.totalCount

        if num_stargazers < self.MIN_STARGAZERS:
            logger.debug("Repository %s has too few stargazers (%d) to analyze.", target_spec.repo_full_name(),
                         num_stargazers)
            return HeuristicRunResult.PASSED()

        if num_stargazers > self.MAX_STARGAZERS:
            logger.debug("Repository %s has too many stargazers (%d) to analyze, limiting to %d.",
                         target_spec.repo_full_name(), num_stargazers, self.MAX_STARGAZERS)
            all_stargazers = all_stargazers[:self.MAX_STARGAZERS]

        logger.info("Analyzing the creation date of %d stargazers", num_stargazers)
        stargazers_by_join_day = {}
        for stargazer in all_stargazers:
            user_joined_day = stargazer.created_at.strftime("%Y-%m-%d")
            if user_joined_day not in stargazers_by_join_day:
                stargazers_by_join_day[user_joined_day] = 0
            stargazers_by_join_day[user_joined_day] += 1

        # Now compute the count for each join day
        for join_day in stargazers_by_join_day:
            pct_joined_on_that_day = 100 * stargazers_by_join_day[join_day] / num_stargazers
            if pct_joined_on_that_day >= self.THRESHOLD_PERCENT:
                additional_details = (
                    f"Repository {target_spec.repo_full_name()} has {stargazers_by_join_day[join_day]} stargazers "
                    f"({pct_joined_on_that_day} %) who joined on the same day, {join_day}."
                )
                return HeuristicRunResult.TRIGGERED(additional_details=additional_details)

        return HeuristicRunResult.PASSED()
