from __future__ import annotations

import os
import re
import sys
from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository
from simple_logger.logger import get_logger

LOGGER = get_logger(name="pr_labeler")


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
    size: int = get_pr_size(pr=pr)
    size_label: str = get_size_label(size=size)

    for label in pr.labels:
        if label.name == size_label:
            LOGGER.info(f"Label {label.name} already set")
            return

        if label.name.lower().startswith("size/"):
            LOGGER.info(f"Removing label {label.name}")
            pr.remove_from_labels(label.name)

    LOGGER.info(f"New label: {size_label}")
    pr.add_to_labels(size_label)


def add_remove_pr_label(pr: PullRequest, comment_body: str) -> None:
    supported_labels: set[str] = {"/wip", "/lgtm", "/verified", "/hold"}

    # Searches for `supported_labels` in PR comment and splits to tuples; index 0 is label, index 1 (optional) `cancel`
    user_labels: list[tuple[str, str]] = re.findall(
        rf"({'|'.join(supported_labels)})(\s*cancel)?", comment_body.lower()
    )

    # In case of the same label appears multiple times, the last one is used
    labels: dict[str, str] = {}
    for _label in user_labels:
        labels[_label[0]] = _label[1]

    for label, action in labels.items():
        if action == "cancel":
            LOGGER.info(f"Removing label {label}")
            pr.remove_from_labels(label)
        else:
            LOGGER.info(f"Adding label {label}")
            pr.add_to_labels(label)


def main() -> None:
    github_token: str | None = os.getenv("GITHUB_TOKEN")
    if not github_token:
        sys.exit("`GITHUB_TOKEN` is not set")

    repo_name: str = os.environ["GITHUB_REPOSITORY"]

    pr_number: int | None = int(os.getenv("GITHUB_PR_NUMBER"))
    if not pr_number:
        sys.exit("`GITHUB_PR_NUMBER` is not set")

    event_action: str | None = os.getenv("GITHUB_EVENT_ACTION")
    if not event_action:
        sys.exit("`GITHUB_EVENT_ACTION` is not set")

    event_name: str | None = os.getenv("GITHUB_EVENT_NAME")
    if not event_name:
        sys.exit("`GITHUB_EVENT_NAME` is not set")

    action: str | None = os.getenv("ACTION")
    if not action:
        sys.exit("`ACTION` is not set in workflow")

    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))

    LOGGER.info(
        f"pr number: {pr_number}, event_action: {event_action}, event_name: {event_name}, action: {action}"
    )

    comment_body: str | None = None
    labels_action_name: str = "add-remove-labels"

    if action == labels_action_name:
        comment_body: str = os.getenv("COMMENT_BODY")
        if not comment_body:
            sys.exit("`COMMENT_BODY` is not set")

    gh_client: Github = Github(github_token)
    repo: Repository = gh_client.get_repo(repo_name)
    pr: PullRequest = repo.get_pull(pr_number)

    if action == "size-labeler":
        set_pr_size(pr=pr)

    if action == labels_action_name:
        add_remove_pr_label(pr=pr, comment_body=comment_body)


if __name__ == "__main__":
    main()
