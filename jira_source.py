#!/usr/bin/env python3
# Copyright (c) 2024-2026 Sreekanth Harigovindan / AI Quality Lab
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Build a test requirement from a Jira work item via the Atlassian Teamwork Graph CLI (twg)."""

import json
import shutil
import subprocess


def _walk(node):
    """Yield every dict found anywhere within a nested dict/list structure."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _find_first_key(data, key: str):
    """Return the first value found for ``key`` anywhere in nested JSON."""
    for node in _walk(data):
        if key in node:
            return node[key]
    return None


def _adf_to_text(adf) -> str:
    """Join Atlassian Document Format (ADF) "text" leaf nodes into plain text."""
    return "\n".join(node["text"] for node in _walk(adf) if node.get("type") == "text")


def get_requirement_from_jira(key: str) -> str:
    """Fetch a Jira work item via ``twg`` and build a requirement string from it."""
    twg_path = shutil.which("twg")

    result = subprocess.run(
        [twg_path, "jira", "workitem", "get", key, "-o", "json", "--output-summary", "none"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    data = json.loads(result.stdout)

    summary = _find_first_key(data, "summary")

    description = _find_first_key(data, "description")
    if isinstance(description, dict):
        description = _adf_to_text(description)
    description = (description or "").strip()

    requirement = str(summary)
    if description:
        requirement += f"\n\nAcceptance criteria:\n{description}"

    return requirement
