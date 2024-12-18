import os
import sys
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from simple_logger.logger import get_logger

LOGGER = get_logger(name=__name__)


def get_pr_size(pr: PullRequest) -> int:
    excluded_files: set[str] = {".lock", ".md"}
    additions: int = 0

    for file in pr.get_files():
        if not any(file.filename.endswith(pattern) for pattern in excluded_files):
            additions += file.additions + file.deletions

    LOGGER.info(f"PR size: {additions}")
    return additions


def get_size_label(size: int) -> str:
    size_labels: dict[tuple[int, int], str] = {
        (0, 20): "size/xs",
        (21, 50): "size/s",
        (51, 100): "size/m",
        (101, 300): "size/l",
        (301, sys.maxsize): "size/xl",
    }

    for (min_size, max_size), label in size_labels.items():
        if min_size <= size <= max_size:
            return label
    return "size/xl"


def set_pr_size(pr: PullRequest) -> None:
    for label in pr.labels:
        if label.name.startswith("size/"):
            pr.remove_from_labels(label.name)

    size: int = get_pr_size(pr=pr)
    new_label: str = get_size_label(size=size)
    LOGGER.info(f"New label: {new_label}")
    pr.add_to_labels(new_label)


def main() -> None:
    github_token: str = os.environ["GITHUB_TOKEN"]
    repo_name: str = os.environ["GITHUB_REPOSITORY"]
    pr_number: int = int(os.environ["GITHUB_PR_NUMBER"])
    event_action: str = os.environ["GITHUB_EVENT_ACTION"]
    event_name: str = os.environ["GITHUB_EVENT_NAME"]

    gh_client: Github = Github(github_token)
    repo: Repository = gh_client.get_repo(repo_name)
    pr: PullRequest = repo.get_pull(pr_number)

    if event_name == "pull_request" and event_action in ("opened", "synchronize"):
        set_pr_size(pr=pr)

if __name__ == "__main__":
    main()
