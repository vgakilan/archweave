"""Structured diagram data, independent of its input and output formats."""

from dataclasses import dataclass
import re


_NODE_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_DIRECTIONS = {"LR", "RL", "TB", "BT"}
_DIAGRAM_TYPES = {"architecture", "flowchart"}
_NODE_TYPES = {
    "actor",
    "application",
    "service",
    "gateway",
    "database",
    "message_broker",
    "external_system",
}


def _validate_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    if "\n" in value or "\r" in value:
        raise ValueError(f"{field} must be on one line")


@dataclass(frozen=True, slots=True)
class Group:
    id: str
    label: str
    parent_group: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _NODE_ID.fullmatch(self.id):
            raise ValueError(f"Invalid group ID: {self.id!r}")
        _validate_text(self.label, "Group label")
        if self.parent_group is not None and (
            not isinstance(self.parent_group, str)
            or not _NODE_ID.fullmatch(self.parent_group)
        ):
            raise ValueError(f"Invalid parent group ID: {self.parent_group!r}")


@dataclass(frozen=True, slots=True)
class Node:
    id: str
    label: str
    type: str
    group: str | None = None
    icon: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not _NODE_ID.fullmatch(self.id):
            raise ValueError(f"Invalid node ID: {self.id!r}")
        _validate_text(self.label, "Node label")
        if not isinstance(self.type, str) or self.type not in _NODE_TYPES:
            raise ValueError(f"Unsupported node type: {self.type!r}")
        if self.group is not None and (
            not isinstance(self.group, str) or not _NODE_ID.fullmatch(self.group)
        ):
            raise ValueError(f"Invalid node group ID: {self.group!r}")
        if self.icon is not None:
            _validate_text(self.icon, "Node icon")


@dataclass(frozen=True, slots=True)
class Edge:
    source: str
    target: str
    label: str | None = None
    protocol: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not _NODE_ID.fullmatch(self.source):
            raise ValueError(f"Invalid edge source: {self.source!r}")
        if not isinstance(self.target, str) or not _NODE_ID.fullmatch(self.target):
            raise ValueError(f"Invalid edge target: {self.target!r}")
        if self.label is not None:
            _validate_text(self.label, "Edge label")
        if self.protocol is not None:
            _validate_text(self.protocol, "Edge protocol")


@dataclass(frozen=True, slots=True)
class Diagram:
    title: str
    diagram_type: str
    direction: str
    nodes: tuple[Node, ...]
    edges: tuple[Edge, ...]
    groups: tuple[Group, ...] = ()

    def __post_init__(self) -> None:
        _validate_text(self.title, "Diagram title")
        if not isinstance(self.diagram_type, str) or self.diagram_type not in _DIAGRAM_TYPES:
            raise ValueError(f"Unsupported diagram type: {self.diagram_type!r}")
        if not isinstance(self.direction, str) or self.direction not in _DIRECTIONS:
            raise ValueError(f"Invalid flowchart direction: {self.direction!r}")
        if not self.nodes:
            raise ValueError("Diagram must contain at least one node")

        seen: dict[str, int] = {}
        for index, node in enumerate(self.nodes):
            if node.id in seen:
                raise ValueError(
                    f"Duplicate node ID {node.id!r} at nodes[{seen[node.id]}] "
                    f"and nodes[{index}]"
                )
            seen[node.id] = index

        groups_by_id: dict[str, Group] = {}
        for index, group in enumerate(self.groups):
            if group.id in groups_by_id:
                raise ValueError(f"Duplicate group ID {group.id!r} at groups[{index}]")
            if group.id in seen:
                raise ValueError(f"Group ID {group.id!r} conflicts with a node ID")
            groups_by_id[group.id] = group

        for index, group in enumerate(self.groups):
            if group.parent_group is None:
                continue
            if group.parent_group not in groups_by_id:
                raise ValueError(
                    f"groups[{index}].parent_group references unknown group ID "
                    f"{group.parent_group!r}"
                )
            if groups_by_id[group.parent_group].parent_group is not None:
                raise ValueError(
                    f"groups[{index}].parent_group exceeds one level of nesting"
                )

        for index, node in enumerate(self.nodes):
            if node.group is not None and node.group not in groups_by_id:
                raise ValueError(
                    f"nodes[{index}].group references unknown group ID {node.group!r}"
                )

        for index, edge in enumerate(self.edges):
            if edge.source not in seen:
                raise ValueError(
                    f"edges[{index}].source references unknown node ID {edge.source!r}"
                )
            if edge.target not in seen:
                raise ValueError(
                    f"edges[{index}].target references unknown node ID {edge.target!r}"
                )
