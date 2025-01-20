from typing import Dict

LABEL_PREFIX: str = "/"
SIZE_LABEL_PREFIX: str = f"size{LABEL_PREFIX}"
WIP_LABEL_STR: str = "wip"
LGTM_LABEL_STR: str = "lgtm"
VERIFIED_LABEL_STR: str = "verified"
HOLD_LABEL_STR: str = "hold"
APPROVED_BY_LABEL_PREFIX: str = "approved-"
LGTM_BY_LABEL_PREFIX: str = f"{LGTM_LABEL_STR}-"
CHANGED_REQUESTED_BY_LABEL_PREFIX: str = "changes-requested-"
COMMENTED_BY_LABEL_PREFIX: str = "commented-"



SUPPORTED_LABELS: set[str] = {
    f"{LABEL_PREFIX}{WIP_LABEL_STR}",
    f"{LABEL_PREFIX}{LGTM_LABEL_STR}",
    f"{LABEL_PREFIX}{VERIFIED_LABEL_STR}",
    f"{LABEL_PREFIX}{HOLD_LABEL_STR}",
}

CANCEL_ACTION: str = "cancel"
WELCOME_COMMENT: str = f"""
The following are automatically added/executed:
 * PR size label.
 * Run [pre-commit](https://pre-commit.ci/)
 * Run [tox](https://tox.wiki/)

Available user actions:
 * To mark a PR as `WIP`, add `/wip` in a comment. To remove it from the PR comment `/wip cancel` to the PR.
 * To block merging of a PR, add `/hold` in a comment. To un-block merging of PR comment `/hold cancel`.
 * To mark a PR as approved, add `/lgtm` in a comment. To remove, add `/lgtm cancel`.
        `lgtm` label removed on each new commit push.
 * To mark PR as verified comment `/verified` to the PR, to un-verify comment `/verified cancel` to the PR.
        `verified` label removed on each new commit push.

<details>
<summary>Supported labels</summary>

{SUPPORTED_LABELS}
</details>
    """


DEFAULT_LABEL_COLOR = "B60205"
USER_LABELS_DICT: Dict[str, str] = {
    HOLD_LABEL_STR: DEFAULT_LABEL_COLOR,
    VERIFIED_LABEL_STR: "0E8A16",
    WIP_LABEL_STR: DEFAULT_LABEL_COLOR,
    LGTM_LABEL_STR: "0E8A16",
}

STATIC_LABELS_DICT: Dict[str, str] = {
    **USER_LABELS_DICT,
    f"{SIZE_LABEL_PREFIX}L": "F5621C",
    f"{SIZE_LABEL_PREFIX}M": "F09C74",
    f"{SIZE_LABEL_PREFIX}S": "0E8A16",
    f"{SIZE_LABEL_PREFIX}XL": "D93F0B",
    f"{SIZE_LABEL_PREFIX}XS": "ededed",
    f"{SIZE_LABEL_PREFIX}XXL": DEFAULT_LABEL_COLOR,
}

DYNAMIC_LABELS_DICT: Dict[str, str] = {
    LGTM_BY_LABEL_PREFIX: "DCED6F",
    COMMENTED_BY_LABEL_PREFIX: "D93F0B",
    CHANGED_REQUESTED_BY_LABEL_PREFIX: "F5621C",
}

ALL_LABELS_DICT: Dict[str, str] = {**STATIC_LABELS_DICT, **DYNAMIC_LABELS_DICT}
