"""Select presentation views from a validated diagram without changing its facts."""

from dataclasses import dataclass, replace
import json
from pathlib import Path
import re

from diagram_generator.models import Diagram, Edge, Group


_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
_DIRECTIONS = {"LR", "RL", "TB", "BT"}


@dataclass(frozen=True, slots=True)
class ViewGroup:
    id: str
    label: str
    node_ids: tuple[str, ...]
    parent_group: str | None = None


@dataclass(frozen=True, slots=True)
class ViewPlan:
    name: str
    purpose: str
    included_node_ids: tuple[str, ...]
    included_edges: tuple[Edge, ...]
    groups: tuple[ViewGroup, ...]
    preferred_direction: str
    primary_flow: tuple[str, ...]
    external_system_placement: str | None
    max_recommended_nodes: int


@dataclass(frozen=True, slots=True)
class DiagramPlan:
    views: tuple[ViewPlan, ...]


def _nonempty(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonempty string")
    return value


def _id(value: object, field: str) -> str:
    if not isinstance(value, str) or _ID.fullmatch(value) is None:
        raise ValueError(f"{field} must be a valid ID")
    return value


def _unique(values: tuple[str, ...], field: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{field} contains duplicate IDs")


def load_diagram_plan(path: str | Path) -> DiagramPlan:
    """Load a view plan; source-model references are checked by project_view."""
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"views"}:
        raise ValueError("Diagram plan must contain exactly 'views'")
    if not isinstance(data["views"], list) or not data["views"]:
        raise ValueError("Diagram plan must contain at least one view")

    views = []
    required = {
        "name", "purpose", "included_node_ids", "included_edges", "groups",
        "preferred_direction", "primary_flow", "external_system_placement",
        "max_recommended_nodes",
    }
    for index, item in enumerate(data["views"]):
        if not isinstance(item, dict) or set(item) != required:
            raise ValueError(f"views[{index}] has missing or unsupported fields")
        name = _id(item["name"], f"views[{index}].name")
        purpose = _nonempty(item["purpose"], f"views[{index}].purpose")
        direction = item["preferred_direction"]
        if not isinstance(direction, str) or direction not in _DIRECTIONS:
            raise ValueError(f"views[{index}].preferred_direction is unsupported")
        maximum = item["max_recommended_nodes"]
        if type(maximum) is not int or maximum < 1:
            raise ValueError(f"views[{index}].max_recommended_nodes must be positive")
        placement = item["external_system_placement"]
        if placement is not None:
            _id(placement, f"views[{index}].external_system_placement")
        for field in ("included_node_ids", "included_edges", "groups", "primary_flow"):
            if not isinstance(item[field], list):
                raise ValueError(f"views[{index}].{field} must be an array")
        node_ids = tuple(
            _id(value, "included_node_ids item") for value in item["included_node_ids"]
        )
        flow = tuple(_id(value, "primary_flow item") for value in item["primary_flow"])
        edges = []
        for raw in item["included_edges"]:
            if (
                not isinstance(raw, dict)
                or not {"source", "target"} <= set(raw)
                or set(raw) - {"source", "target", "label", "protocol"}
            ):
                raise ValueError(f"views[{index}].included_edges has an invalid relationship")
            edges.append(Edge(**raw))
        groups = []
        for raw in item["groups"]:
            if (
                not isinstance(raw, dict)
                or not {"id", "label", "node_ids"} <= set(raw)
                or set(raw) - {"id", "label", "node_ids", "parent_group"}
            ):
                raise ValueError(f"views[{index}].groups has an invalid group")
            if not isinstance(raw["node_ids"], list):
                raise ValueError(f"views[{index}].groups.node_ids must be an array")
            groups.append(
                ViewGroup(
                    id=_id(raw["id"], "group.id"),
                    label=_nonempty(raw["label"], "group.label"),
                    node_ids=tuple(
                        _id(value, "group.node_ids item") for value in raw["node_ids"]
                    ),
                    parent_group=raw.get("parent_group"),
                )
            )
        views.append(
            ViewPlan(
                name=name,
                purpose=purpose,
                included_node_ids=node_ids,
                included_edges=tuple(edges),
                groups=tuple(groups),
                preferred_direction=direction,
                primary_flow=flow,
                external_system_placement=placement,
                max_recommended_nodes=maximum,
            )
        )
    names = tuple(view.name for view in views)
    _unique(names, "view names")
    return DiagramPlan(tuple(views))


def project_view(source: Diagram, plan: ViewPlan) -> Diagram:
    """Filter a source model and apply view-only grouping and layout metadata."""
    selected = plan.included_node_ids
    if not selected:
        raise ValueError(f"View {plan.name!r} must include at least one node")
    _unique(selected, f"View {plan.name!r} nodes")
    if len(selected) > plan.max_recommended_nodes:
        raise ValueError(f"View {plan.name!r} exceeds its recommended node maximum")
    source_nodes = {node.id: node for node in source.nodes}
    unknown = set(selected) - source_nodes.keys()
    if unknown:
        raise ValueError(f"View {plan.name!r} references unknown nodes: {sorted(unknown)}")

    source_edges = set(source.edges)
    if len(plan.included_edges) != len(set(plan.included_edges)):
        raise ValueError(f"View {plan.name!r} repeats a relationship")
    for edge in plan.included_edges:
        if edge not in source_edges:
            raise ValueError(
                f"View {plan.name!r} contains a relationship absent from the source: {edge}"
            )
        if edge.source not in selected or edge.target not in selected:
            raise ValueError(f"View {plan.name!r} has an edge outside its included nodes")

    groups_by_id: dict[str, ViewGroup] = {}
    assignments: dict[str, str] = {}
    for group in plan.groups:
        if group.id in groups_by_id:
            raise ValueError(f"View {plan.name!r} repeats group ID {group.id!r}")
        groups_by_id[group.id] = group
        _unique(group.node_ids, f"Group {group.id!r} nodes")
        for node_id in group.node_ids:
            if node_id not in selected:
                raise ValueError(f"Group {group.id!r} contains a node outside the view")
            if node_id in assignments:
                raise ValueError(f"Node {node_id!r} belongs to multiple view groups")
            assignments[node_id] = group.id

    externals = {
        node_id for node_id in selected
        if source_nodes[node_id].type == "external_system"
    }
    placement = plan.external_system_placement
    if externals:
        if placement not in groups_by_id:
            raise ValueError(f"View {plan.name!r} needs a boundary group for external systems")
        if any(assignments.get(node_id) != placement for node_id in externals):
            raise ValueError(
                f"View {plan.name!r} has an external system outside its boundary group"
            )
        if any(
            source_nodes[node_id].type != "external_system"
            for node_id in groups_by_id[placement].node_ids
        ):
            raise ValueError(f"View {plan.name!r} mixes internal nodes into its external boundary")
    elif placement is not None:
        raise ValueError(f"View {plan.name!r} declares external placement without external nodes")

    if len(plan.primary_flow) != len(set(plan.primary_flow)) or any(
        node_id not in selected for node_id in plan.primary_flow
    ):
        raise ValueError(f"View {plan.name!r} has an invalid primary flow")
    edge_pairs = {(edge.source, edge.target) for edge in plan.included_edges}
    if any(pair not in edge_pairs for pair in zip(plan.primary_flow, plan.primary_flow[1:])):
        raise ValueError(f"View {plan.name!r} primary flow contains an unstated relationship")

    nodes = tuple(
        replace(source_nodes[node_id], group=assignments.get(node_id))
        for node_id in selected
    )
    groups = tuple(Group(group.id, group.label, group.parent_group) for group in plan.groups)
    return Diagram(
        title=f"{source.title}: {plan.name.replace('_', ' ').title()}",
        diagram_type=source.diagram_type,
        direction=plan.preferred_direction,
        nodes=nodes,
        edges=plan.included_edges,
        groups=groups,
    )
