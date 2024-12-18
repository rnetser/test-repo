import os
import sys
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from simple_logger.logger import get_logger

LOGGER = get_logger(name=__name__)

SIZE_LABELS: dict[tuple[int, int], str] = {
    (0, 20): "size/xs",
    (21, 50): "size/s",
    (51, 100): "size/m",
    (101, 300): "size/l",
    (301, sys.maxsize): "size/xl",
}

EXCLUDED_FILES: set[str] = {".lock", ".md"}


def get_pr_size(pr: PullRequest) -> int:
    additions: int = 0
    for file in pr.get_files():
        if not any(file.filename.endswith(pattern) for pattern in EXCLUDED_FILES):
            additions += file.additions + file.deletions

    LOGGER.info(f"PR size: {additions}")
    return additions


def get_size_label(size: int) -> str:
    for (min_size, max_size), label in SIZE_LABELS.items():
        if min_size <= size <= max_size:
            return label
    return "size/xl"


def main() -> None:
    github_token: str = os.environ["GITHUB_TOKEN"]
    repo_name: str = os.environ["GITHUB_REPOSITORY"]
    pr_number: int = int(os.environ["GITHUB_PR_NUMBER"])

    gh_client: Github = Github(github_token)
    repo: Repository = gh_client.get_repo(repo_name)
    pr: PullRequest = repo.get_pull(pr_number)

    for label in pr.labels:
        if label.name.startswith("size/"):
            pr.remove_from_labels(label.name)

    size: int = get_pr_size(pr)
    new_label: str = get_size_label(size)
    LOGGER.info(f"New label: {new_label}")
    pr.add_to_labels(new_label)


if __name__ == "__main__":
    main()
