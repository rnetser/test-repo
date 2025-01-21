from __future__ import annotations

import os
import re
import sys
from github import Github, UnknownObjectException
from github.PullRequest import PullRequest
from github.Repository import Repository
from simple_logger.logger import get_logger
from constants import (
    ALL_LABELS_DICT,
    CANCEL_ACTION,
    CHANGED_REQUESTED_BY_LABEL_PREFIX,
    COMMENTED_BY_LABEL_PREFIX,
    DEFAULT_LABEL_COLOR,
    LABEL_PREFIX,
    LGTM_BY_LABEL_PREFIX,
    LGTM_LABEL_STR,
    SIZE_LABEL_PREFIX,
    SUPPORTED_LABELS,
    VERIFIED_LABEL_STR,
    WELCOME_COMMENT,
)

LOGGER = get_logger(name="pr_labeler")


def get_pr_size(pr: PullRequest) -> int:
    additions: int = 0

    for file in pr.get_files():
        additions += file.additions + file.deletions

    LOGGER.info(f"PR size: {additions}")
    return additions


def get_size_label(size: int) -> str:
    xxl_size = f"{SIZE_LABEL_PREFIX}xxl"

    size_labels: dict[tuple[int, int], str] = {
        (0, 20): f"{SIZE_LABEL_PREFIX}xs",
        (21, 50): f"{SIZE_LABEL_PREFIX}s",
        (51, 100): f"{SIZE_LABEL_PREFIX}m",
        (101, 300): f"{SIZE_LABEL_PREFIX}l",
        (301, 1000): f"{SIZE_LABEL_PREFIX}xl",
        (1001, sys.maxsize): xxl_size,
    }

    for (min_size, max_size), label in size_labels.items():
        if min_size <= size <= max_size:
            return label
    return xxl_size


def add_pr_label(repository: Repository, pr: PullRequest, label: str) -> None:
    set_label_in_repository(repository=repository, label=label)

    LOGGER.info(f"New label: {label}")
    pr.add_to_labels(label)


def set_label_in_repository(repository: Repository, label: str) -> None:
    label_color = [
        label_color
        for label_prefix, label_color in ALL_LABELS_DICT.items()
        if label.startswith(label_prefix)
    ]
    label_color = label_color[0] if label_color else DEFAULT_LABEL_COLOR

    repo_labels = {_label.name: _label.color for _label in repository.get_labels()}
    LOGGER.info(f"repo labels: {repo_labels}")

    try:
        if _repo_label := repository.get_label(name=label):
            if _repo_label.color != label_color:
                LOGGER.info(f"Edit repository label: {label}, color: {label_color}")
                _repo_label.edit(name=_repo_label.name, color=label_color)

    except UnknownObjectException:
        LOGGER.info(f"Add repository label: {label}, color: {label_color}")
        repository.create_label(name=label, color=label_color)


def set_pr_size(pr: PullRequest, repository: Repository) -> None:
    size: int = get_pr_size(pr=pr)
    size_label: str = get_size_label(size=size)

    for label in pr.labels:
        if label.name == size_label:
            LOGGER.info(f"Label {label.name} already set")
            return

        if label.name.lower().startswith(SIZE_LABEL_PREFIX):
            LOGGER.info(f"Removing label {label.name}")
            pr.remove_from_labels(label.name)

    add_pr_label(repository=repository, pr=pr, label=size_label)


def add_remove_pr_labels(
    pr: PullRequest,
    repository: Repository,
    event_name: str,
    event_action: str,
    comment_body: str = "",
    user_login: str = "",
    review_state: str = "",
) -> None:
    if comment_body and WELCOME_COMMENT in comment_body:
        LOGGER.info(f"Welcome message found in PR {pr.title}. Not processing")
        return

    LOGGER.info(
        f"add_remove_pr_label comment_body: {comment_body} event_name:{event_name} "
        f"event_action: {event_action} review_state {review_state}"
    )

    pr_labels = [label.name for label in pr.labels]
    LOGGER.info(f"PR labels: {pr_labels}")

    # Remove labels on new commit
    if event_action == "synchronize":
        LOGGER.info("Synchronize event")
        for label in pr_labels:
            LOGGER.info(f"Processing label: {label}")
            if (
                label.lower() == VERIFIED_LABEL_STR
                or label.lower().startswith(LGTM_BY_LABEL_PREFIX)
                or label.lower().startswith(CHANGED_REQUESTED_BY_LABEL_PREFIX)
            ):
                LOGGER.info(f"Removing label {label}")
                pr.remove_from_labels(label)
        return

    elif event_name == "issue_comment":
        issue_comment_label_actions(
            comment_body=comment_body,
            event_action=event_action,
            event_name=event_name,
            pr=pr,
            pr_labels=pr_labels,
            repository=repository,
            user_login=user_login,
        )

        return

    elif event_name == "pull_request_review":
        pull_request_review_label_actions(
            event_name=event_name,
            pr=pr,
            pr_labels=pr_labels,
            repository=repository,
            review_state=review_state,
            user_login=user_login,
        )

        return

    LOGGER.warning("`add_remove_pr_label` called without a supported event")


def pull_request_review_label_actions(
    event_name: str,
    pr: PullRequest,
    pr_labels: list[str],
    repository: Repository,
    review_state: str,
    user_login: str,
) -> None:
    LOGGER.info(f"{event_name} event, state: {review_state}")

    lgtm_label = f"{LGTM_BY_LABEL_PREFIX}{user_login}"
    change_requested_label = f"{CHANGED_REQUESTED_BY_LABEL_PREFIX}{user_login}"

    label_to_remove = None
    label_to_add = None

    if review_state == "approved":
        label_to_remove = change_requested_label
        label_to_add = lgtm_label

    elif review_state == "changes_requested":
        label_to_add = change_requested_label
        label_to_remove = lgtm_label

    elif review_state == "commented":
        label_to_add = f"{COMMENTED_BY_LABEL_PREFIX}{user_login}"

    if label_to_add and label_to_add not in pr_labels:
        add_pr_label(repository=repository, pr=pr, label=label_to_add)

    if label_to_remove and label_to_remove in pr_labels:
        LOGGER.info(f"Removing review label {label_to_add}")
        pr.remove_from_labels(label_to_remove)


def issue_comment_label_actions(
    comment_body: str,
    event_action: str,
    event_name: str,
    pr: PullRequest,
    pr_labels: list[str],
    repository: Repository,
    user_login: str,
) -> None:
    LOGGER.info(f"{event_name} event")
    # Searches for `supported_labels` in PR comment and splits to tuples;
    # index 0 is label, index 1 (optional) `cancel`
    if user_requested_labels := re.findall(
        rf"({'|'.join(SUPPORTED_LABELS)})\s*(cancel)?", comment_body.lower()
    ):
        LOGGER.info(f"User labels: {user_requested_labels}")

        # In case of the same label appears multiple times, the last one is used
        labels: dict[str, dict[str, bool]] = {}
        for _label in user_requested_labels:
            labels[_label[0].replace(LABEL_PREFIX, "")] = {
                CANCEL_ACTION: _label[1] == CANCEL_ACTION
            }

        LOGGER.info(f"Processing labels: {labels}")
        for label, action in labels.items():
            if label == LGTM_LABEL_STR:
                label = f"{LGTM_BY_LABEL_PREFIX}{user_login}"

            label_in_pr = any([label == _label.lower() for _label in pr_labels])
            LOGGER.info(f"Processing label: {label}, action: {action}")

            if action[CANCEL_ACTION] or event_action == "deleted":
                if label_in_pr:
                    LOGGER.info(f"Removing label {label}")
                    pr.remove_from_labels(label)

            elif not label_in_pr:
                add_pr_label(repository=repository, pr=pr, label=label)

    else:
        commented_by_label = f"{COMMENTED_BY_LABEL_PREFIX}{user_login}"
        if commented_by_label not in pr_labels:
            add_pr_label(repository=repository, pr=pr, label=commented_by_label)


def add_welcome_comment(pr: PullRequest) -> None:
    pr.create_issue_comment(body=WELCOME_COMMENT)


def main() -> None:
    labels_action_name: str = "add-remove-labels"
    pr_size_action_name: str = "add-pr-size-label"
    welcome_comment_action_name: str = "add-welcome-comment"
    supported_actions: set[str] = {
        pr_size_action_name,
        labels_action_name,
        welcome_comment_action_name,
    }
    action: str | None = os.getenv("ACTION")

    if not action or action not in supported_actions:
        sys.exit(
            "`ACTION` is not set in workflow or is not supported. Supported actions: {supported_actions}"
        )

    github_token: str | None = os.getenv("GITHUB_TOKEN")
    if not github_token:
        sys.exit("`GITHUB_TOKEN` is not set")

    repo_name: str = os.environ["GITHUB_REPOSITORY"]

    pr_number: int = int(os.getenv("GITHUB_PR_NUMBER", 0))
    if not pr_number:
        sys.exit("`GITHUB_PR_NUMBER` is not set")

    event_action: str | None = os.getenv("GITHUB_EVENT_ACTION")
    if not event_action:
        sys.exit("`GITHUB_EVENT_ACTION` is not set")

    event_name: str | None = os.getenv("GITHUB_EVENT_NAME")
    if not event_name:
        sys.exit("`GITHUB_EVENT_NAME` is not set")

    LOGGER.info(
        f"pr number: {pr_number}, event_action: {event_action}, event_name: {event_name}, action: {action}"
    )

    comment_body: str = ""
    user_login: str = ""
    review_state: str = ""

    if action == labels_action_name and event_name in (
        "issue_comment",
        "pull_request_review",
    ):
        user_login = os.getenv("GITHUB_USER_LOGIN")
        if not user_login:
            sys.exit("`GITHUB_USER_LOGIN` is not set")

        if event_name == "issue_comment":
            comment_body = os.getenv("COMMENT_BODY") or comment_body
            if not comment_body:
                sys.exit("`COMMENT_BODY` is not set")

        if event_name == "pull_request_review":
            review_state = os.getenv("GITHUB_EVENT_REVIEW_STATE")
            if not review_state:
                sys.exit("`GITHUB_EVENT_REVIEW_STATE` is not set")

    gh_client: Github = Github(github_token)
    repo: Repository = gh_client.get_repo(repo_name)
    pr: PullRequest = repo.get_pull(pr_number)

    if action == pr_size_action_name:
        set_pr_size(pr=pr, repository=repo)

    if action == labels_action_name:
        add_remove_pr_labels(
            pr=pr,
            event_name=event_name,
            event_action=event_action,
            comment_body=comment_body,
            user_login=user_login,
            repository=repo,
            review_state=review_state,
        )

    if action == welcome_comment_action_name:
        add_welcome_comment(pr=pr)


if __name__ == "__main__":
    main()
