"""Starting point for an embedded EmberVault module."""


def describe() -> dict[str, str]:
    """Return a read-only description for the Control Center shell."""
    return {
        "id": "embervault.replace-me",
        "execution": "embedded",
        "mutation": "read-only",
        "capability_state": "research-only",
    }
