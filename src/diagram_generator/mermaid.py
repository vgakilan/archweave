"""Generate architecture Mermaid from selected requirement facts."""

from html import escape


_SHAPES = {
    "actor": ("([", "])"),
    "application": ("(", ")"),
    "service": ("[", "]"),
    "gateway": ("{", "}"),
    "database": ("[(", ")]"),
    "external_system": ("[[", "]]"),
    "message_broker": ("{{", "}}"),
}


def _label(value: str) -> str:
    return escape(value, quote=True).replace("|", "#124;")


def generate_architecture(nodes: list[dict], edges: list[dict], direction: str) -> str:
    """Render selected nodes and their stated edges as a flowchart."""
    lines = [f"flowchart {direction}"]
    for node in nodes:
        opening, closing = _SHAPES[node["type"]]
        lines.append(f'    {node["id"]}{opening}"{_label(node["name"])}"{closing}')
    for edge in edges:
        description = edge["action"]
        if edge.get("protocol"):
            description += f" ({edge['protocol']})"
        lines.append(
            f'    {edge["source"]} -->|"{_label(description)}"| {edge["target"]}'
        )
    return "\n".join(lines) + "\n"
