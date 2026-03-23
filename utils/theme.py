"""Shared theme utilities — single source of truth for theme access."""


def T(theme: dict, key: str) -> str:
    """Get a color value from the theme dict. Returns white as fallback."""
    return theme.get(key, '#ffffff')
