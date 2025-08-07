import logging
import sys

import github.Auth
import requests_cache

from ghbuster.heuristics import MetadataHeuristic, ALL_HEURISTICS, TargetType
from .cli import CliArguments, parse_and_validate_args
from .github_repo_scanner import GitHubScanner

from .output_formatter import OutputFormatter

from ghbuster.heuristics import UserLooksLegit

def setup_logging(log_level: int):
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
    logging.getLogger("requests_cache").setLevel(logging.INFO)


def setup_caching():
    requests_cache.install_cache('github_cache', expire_after=3600)

def resolve_heuristics(included_heuristics: set[str], excluded_heuristics: set[str]) -> list[MetadataHeuristic]:
    heuristics = []
    for heuristic in ALL_HEURISTICS:
        if included_heuristics:
            if heuristic.id() in included_heuristics:
                heuristics.append(heuristic)
        elif excluded_heuristics:
            if heuristic.id() not in included_heuristics:
                heuristics.append(heuristic)
        else:
            heuristics.append(heuristic)
    return heuristics

def main(args: CliArguments):
    setup_logging(args.log_level)
    setup_caching()
    github_client = github.Github(auth=github.Auth.Token(args.github_token))
    heuristics_to_run = resolve_heuristics(args.included_heuristics, args.excluded_heuristics)

    if args.target_spec.target_type == TargetType.USER:
        smoke_test = UserLooksLegit().run(github_client, args.target_spec)
        if smoke_test.triggered:
            logging.info("An initial analysis indicates that the GitHub user %s is likely legitimate: %s",
                         args.target_spec.username, smoke_test.additional_details)
            if not args.force:
                logging.info("Exiting early without running all heuristics. Use --force to bypass")
            return

    scanner = GitHubScanner(args.target_spec, github_client, heuristics=heuristics_to_run)
    scanner.ensure_authenticated()
    scanner.validate_target_spec()
    results = scanner.scan()
    output = OutputFormatter().format_results(args.target_spec, results)
    print(output)

def cli_entrypoint():
    try:
        main(parse_and_validate_args(sys.argv[1:]))
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli_entrypoint()

