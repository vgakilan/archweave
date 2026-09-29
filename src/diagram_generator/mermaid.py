"""Render structured diagrams as Mermaid source."""

from html import escape

from diagram_generator.icons import resolve_icon
from diagram_generator.models import Diagram, Node


_NODE_SHAPES = {
    "actor": ("([", "])"),
    "application": ("(", ")"),
    "service": ("[", "]"),
    "gateway": ("{", "}"),
    "database": ("[(", ")]"),
    "external_system": ("[[", "]]"),
    "message_broker": ("{{", "}}"),
}

_NODE_STYLES = {
    "actor": "fill:#eef2ff,stroke:#4f46e5,stroke-width:1.5px,color:#1e1b4b",
    "application": "fill:#eff6ff,stroke:#2563eb,stroke-width:1.5px,color:#172554",
    "service": "fill:#ecfdf5,stroke:#059669,stroke-width:1.5px,color:#064e3b",
    "gateway": "fill:#fff7ed,stroke:#d97706,stroke-width:1.5px,color:#78350f",
    "database": "fill:#f0fdfa,stroke:#0f766e,stroke-width:1.5px,color:#134e4a",
    "external_system": "fill:#f8fafc,stroke:#64748b,stroke-width:1.5px,color:#0f172a",
    "message_broker": "fill:#faf5ff,stroke:#7e22ce,stroke-width:1.5px,color:#581c87",
}

_GROUP_STYLES = {
    "group_boundary": "fill:#f8fafc,stroke:#94a3b8,stroke-width:1px,color:#334155",
    "group_nested": "fill:#ffffff,stroke:#cbd5e1,stroke-width:1px,color:#475569",
}


def _label(value: str) -> str:
    return escape(value, quote=True).replace("|", "#124;")


def _node_line(node: Node, indent: str = "    ") -> str:
    label = _label(node.label)
    icon = resolve_icon(node.type, node.icon)
    if icon is not None:
        return (
            f'{indent}{node.id}@{{ shape: icon, icon: "{icon}", '
            f'label: "{label}", form: "rounded", h: 48 }}'
        )
    opening, closing = _NODE_SHAPES[node.type]
    return f'{indent}{node.id}{opening}"{label}"{closing}'


def generate_mermaid(diagram: Diagram) -> str:
    """Generate a deterministic Mermaid flowchart from a validated diagram."""
    lines = [f"flowchart {diagram.direction}"]

    if not diagram.groups:
        lines.extend(_node_line(node) for node in diagram.nodes)
    else:
        lines.extend(_node_line(node) for node in diagram.nodes if node.group is None)
        for group in diagram.groups:
            if group.parent_group is not None:
                continue
            lines.append(f'    subgraph {group.id}["{_label(group.label)}"]')
            lines.append(f"        direction {diagram.direction}")
            lines.extend(
                _node_line(node, "        ")
                for node in diagram.nodes
                if node.group == group.id
            )
            for child in diagram.groups:
                if child.parent_group != group.id:
                    continue
                lines.append(f'        subgraph {child.id}["{_label(child.label)}"]')
                lines.append(f"            direction {diagram.direction}")
                lines.extend(
                    _node_line(node, "            ")
                    for node in diagram.nodes
                    if node.group == child.id
                )
                lines.append("        end")
            lines.append("    end")

    lines.append("")
    for edge in diagram.edges:
        if edge.label is not None and edge.protocol is not None:
            description = f"{edge.label} ({edge.protocol})"
        else:
            description = edge.label or edge.protocol

        if description is None:
            lines.append(f"    {edge.source} --> {edge.target}")
        else:
            lines.append(f"    {edge.source} -->|{_label(description)}| {edge.target}")

    lines.append("")
    for node_type, style in _NODE_STYLES.items():
        lines.append(f"    classDef type_{node_type} {style};")
    for node_type in _NODE_STYLES:
        ids = [node.id for node in diagram.nodes if node.type == node_type]
        if ids:
            lines.append(f"    class {','.join(ids)} type_{node_type};")

    if diagram.groups:
        for class_name, style in _GROUP_STYLES.items():
            lines.append(f"    classDef {class_name} {style};")
        for group in diagram.groups:
            class_name = "group_boundary" if group.parent_group is None else "group_nested"
            lines.append(f"    class {group.id} {class_name};")

    return "\n".join(lines) + "\n"
