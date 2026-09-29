# Diagram Planner

## Responsibility

Plan focused presentation views from an already validated structured Diagram.
The extracted model remains the source of truth. Planning may select nodes and
edges, choose layout direction, and group selected nodes for readability. It
must not add or alter actors, systems, technologies, labels, protocols, or
relationships in that model.

## Plan contract

Write a JSON plan with a `views` array. Each view defines:

- `name`: unique output filename stem.
- `purpose`: what the view helps a reader understand.
- `included_node_ids`: IDs from the source Diagram.
- `included_edges`: exact source relationships, including any label and protocol.
- `groups`: view-only layers or boundaries, each with `id`, `label`, `node_ids`,
  and optional `parent_group`. Group membership must be supported by stated
  component roles or boundaries. These do not edit the source model.
- `preferred_direction`: `LR`, `RL`, `TB`, or `BT`.
- `primary_flow`: an ordered sequence of node IDs. Every consecutive pair must
  have an included source edge. Use an empty array when no path is stated.
- `external_system_placement`: the ID of a separate external-boundary group,
  or `null` when the view contains no external system. This expresses a logical
  boundary; Mermaid may not guarantee exact page coordinates.
- `max_recommended_nodes`: a positive view-size limit. A view exceeding it is
  rejected so the plan can be split.

## Planning rules

1. Prefer multiple focused diagrams over one crowded graph. A context view
   should show only major systems and actors. A detailed view may show named
   internal services.
2. Select only source-model nodes and exact source-model edges. Do not create
   connectivity for layout. Disconnected nodes may be intentional when the
   requirement does not state communication direction.
3. Place external systems in a separate boundary group. Group infrastructure
   separately from business services. Place data stores near owning or
   consuming services only when that ownership or consumption is supported.
4. Include messaging infrastructure in a view only where it participates in
   a stated relationship. Do not leave a broker as an isolated random node.
5. Avoid long single-column stacks and excessive crossing edges by splitting
   views and selecting concise groups. Prefer `LR` for service architecture
   where reasonable. Use `TB` only when a real hierarchy benefits from it.
6. Treat groups and direction as presentation choices, not new architecture
   facts. Keep the original model JSON unchanged.

## Rendering

Run `python scripts/generate_views.py <model-json> <plan-json>`. The command
validates the source model and all views before rendering each view with the
existing Mermaid generator and local CLI. Review each output for readability
and report any limitation caused by missing source relationships.
