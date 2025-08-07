import logging
import os
import re
from argparse import ArgumentParser

from . import TargetType, TargetSpec


def _cli() -> ArgumentParser:
    parser = ArgumentParser(
        prog="ghbuster",
        exit_on_error=False,
        description="Identify inauthentic GitHub accounts and repositories",
    )

    parser.add_argument("target", type=str,
                        help="Target GitHub repository or user to scan, e.g., 'owner/repo', `username`, or 'https://github.com/owner/repo'.")
    parser.add_argument("--github-token", type=str,
                        help="GitHub token for authentication. If not provided, the GITHUB_TOKEN environment variable is used",
                        required=False, default=os.environ.get("GITHUB_TOKEN"))
    parser.add_argument("--debug", action="store_true", help="Enable debug logging", dest="enable_debug", default=False)
    parser.add_argument("--include", nargs="+", help="Heuristics to include (any other heuristic will not be ran)",
                        default=[])
    parser.add_argument("--exclude", nargs="+", help="Heuristics to exclude", default=[])
    parser.add_argument("--force", action="store_true", default=False)
    return parser


class CliArguments:
    target_spec: TargetSpec
    github_token: str
    log_level: int
    excluded_heuristics: set[str]
    included_heuristics: set[str]
    force: bool


def parse_and_validate_args(args) -> CliArguments:
    args = _cli().parse_args(args)
    cli_args = CliArguments()

    # Determine target type and parse repository or user
    normalized_target = args.target.strip().lower()
    github_url_prefix = "https://github.com/"
    if normalized_target.startswith(github_url_prefix):
        normalized_target = normalized_target[len(github_url_prefix):]

    if '/' in normalized_target:
        # It's a repository
        parts = normalized_target.split('/')
        if len(parts) != 2:
            raise ValueError("Invalid repository format. Expected 'owner/repo'.")
        cli_args.target_spec = TargetSpec(target_type=TargetType.REPOSITORY, username=parts[0], repo_name=parts[1])
    else:
        # It's a user
        if not re.match(r'^[a-zA-Z0-9-]+$', normalized_target):
            # "Username may only contain alphanumeric characters or single hyphens, and cannot begin or end with a hyphen." (from the GitHub homepage)
            raise ValueError("Invalid GitHub username format")
        cli_args.target_spec = TargetSpec(target_type=TargetType.USER, username=normalized_target)

    # Github token
    cli_args.github_token = args.github_token
    if cli_args.github_token is None or len(cli_args.github_token) == 0:
        raise ValueError(
            "GitHub token is required. Please provide it via the --github-token argument or set the GITHUB_TOKEN environment variable.")

    # Log level
    cli_args.log_level = logging.DEBUG if args.enable_debug else logging.INFO

    # Heuristics selection
    if args.include and args.exclude:
        raise ValueError("--include and --exclude are mutually exclusive.")
    cli_args.included_heuristics = set(args.include)
    cli_args.excluded_heuristics = set(args.exclude)

    cli_args.force = args.force
    return cli_args
