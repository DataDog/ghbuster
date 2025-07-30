from pyvis.network import Network

from .user_has_low_community_activity import *
from .user_metadata_basic import *

logger = logging.getLogger(__name__)

import networkx as nx

# NOTE: This heuristic is unused and experimental for now.
class Graph(MetadataHeuristic):
    MAX_ITERATIONS = 3

    def id(self) -> str:
        return 'repo.graph'

    def friendly_name(self) -> str:
        return "Test"

    def description(self) -> str:
        return "TODO"

    def target_type(self) -> TargetType:
        return TargetType.REPOSITORY

    def run(self, github_client: github.Github, target_spec: TargetSpec) -> HeuristicRunResult:
        repo = github_client.get_repo(full_name_or_id=target_spec.repo_full_name())
        current_iteration = 1
        current_queue = [repo]
        visited_repos = set()
        visited_users = set()
        graph = nx.Graph()
        while current_iteration <= self.MAX_ITERATIONS and current_queue:
            logger.debug("Starting iteration %d with %d repositories in the queue", current_iteration,
                         len(current_queue))
            next_queue = []
            for repo in current_queue:
                if repo.full_name in visited_repos:
                    continue
                visited_repos.add(repo.full_name)
                logger.debug("Processing repository %s at iteration depth %d", repo.full_name, current_iteration)

                # logic
                graph.add_node(repo.full_name, type='repository')
                graph.add_edge(repo.full_name, repo.owner.login, type='owns')

                try:
                    all_stargazers = repo.get_stargazers_with_dates()
                    all_forks = repo.get_forks()
                    logger.debug("Found %d stargazers and %d forks for repository %s", all_stargazers.totalCount,
                                 all_forks.totalCount, repo.full_name)
                except github.GithubException as e:
                    # Sample error when a repository is still up but has been restricted access to:
                    # github.GithubException.GithubException: Repository access blocked: 403 {"message": "Repository access blocked", "block": {"reason": "tos", "created_at": "2025-06-23T08:05:48Z", "html_url": "https://github.com/tos"}}
                    if e.status in [403, 451] and e.message == 'Repository access blocked':
                        logger.warning(
                            "Repository %s cannot be accessed, most likely disabled due to a breach of ToS. Ignoring",
                            repo.full_name)
                        continue
                    else:
                        raise e

                # If the current repository is a fork, make sure to visit the parent repository as well
                if repo.fork and repo.parent and repo.parent.full_name not in visited_repos:
                    logger.debug("Repository %s is a fork, adding parent repository %s to the queue", repo.full_name,
                                 repo.parent.full_name)
                    next_queue.append(repo.parent)

                users_to_visit_in_next_iteration = set()
                for stargazer in all_stargazers:
                    graph.add_node(stargazer.user.login, type='user')
                    graph.add_edge(stargazer.user.login, repo.full_name, type='stars')
                    # Visit every user who starred the repo
                    users_to_visit_in_next_iteration.add(stargazer.user.login)

                for fork in all_forks:
                    graph.add_edge(fork.owner.login, repo.full_name, type='forks')
                    # Visit every user who forked the repo
                    users_to_visit_in_next_iteration.add(fork.owner.login)

                for user_to_visit in users_to_visit_in_next_iteration:
                    if user_to_visit not in visited_users:
                        visited_users.add(user_to_visit)
                        try:
                            user_repos = github_client.get_user(login=user_to_visit).get_repos(type='owner')
                            repos_to_visit = [r for r in user_repos if r.full_name not in visited_repos]
                            logger.debug("Will visit user %s (%d unvisited repos)", user_to_visit, len(repos_to_visit))
                            next_queue.extend(repos_to_visit)
                        except github.GithubException as e:
                            if e.status == 404:
                                logger.warning("User %s not found (probably taken down), skipping", user_to_visit)
                            else:
                                raise e
            # end logic
            current_queue = next_queue
            current_iteration += 1

        nt = Network('1000px', '100%')
        nt.from_nx(graph)
        for edge in nt.edges:
            if 'type' in edge:
                edge['label'] = edge['type']
        nt.show_buttons()
        nt.write_html('/tmp/graph.html', open_browser=True)

        return HeuristicRunResult.PASSED()
