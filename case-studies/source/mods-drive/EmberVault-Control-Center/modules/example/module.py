"""Minimal embedded-module contract example."""


def describe() -> dict[str, str]:
    return {
        "id": "embervault.example",
        "execution": "embedded",
        "mutation": "read-only",
    }
