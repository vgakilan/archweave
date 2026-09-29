"""Local icon choices for optional Mermaid presentation metadata."""

from functools import lru_cache
import json
from pathlib import Path
import re


ICON_PACKAGES = {
    "lucide": "@iconify-json/lucide",
    "simple-icons": "@iconify-json/simple-icons",
}

GENERIC_ICONS = {
    "actor": "lucide:user-round",
    "application": "lucide:app-window",
    "service": "lucide:server",
    "gateway": "lucide:network",
    "database": "lucide:database",
    "external_system": "lucide:monitor",
    "message_broker": "lucide:messages-square",
}

_ICON_NAME = re.compile(r"([a-z][a-z0-9-]*):([a-z0-9-]+)\Z")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=None)
def _available_icons(prefix: str) -> frozenset[str]:
    package = ICON_PACKAGES.get(prefix)
    if package is None:
        return frozenset()
    path = _PROJECT_ROOT / "node_modules" / package / "icons.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return frozenset()
    return frozenset(data.get("icons", {}))


def _is_available(icon: str) -> bool:
    match = _ICON_NAME.fullmatch(icon)
    return match is not None and match.group(2) in _available_icons(match.group(1))


def resolve_icon(node_type: str, requested_icon: str | None) -> str | None:
    """Resolve an opt-in icon locally, with a generic then shape fallback."""
    if requested_icon is None:
        return None
    generic = GENERIC_ICONS[node_type]
    requested = generic if requested_icon == "generic" else requested_icon
    if _is_available(requested):
        return requested
    return generic if _is_available(generic) else None
