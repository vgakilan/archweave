# Project: Requirement to Diagram

## Goal

Convert natural-language software requirements into structured, reviewable
architecture diagrams. Mermaid is the initial renderer.

## Primary language

Use Python 3.12+. Do not introduce JavaScript application code unless
necessary. Node.js is permitted for local Mermaid CLI tooling.

## Architecture

Requirement → Requirement Analyzer → structured Diagram model → schema/domain
validation → optional Diagram Planner → Mermaid generator → renderer → SVG.

## Design rules

1. The structured model is the source of truth.
2. Never generate Mermaid directly from raw requirements.
3. Separate requirement interpretation, view planning, and rendering.
4. Rendering failures must fail the process.
5. Prefer simple focused views over crowded diagrams.
6. Put generated models and diagrams under `diagrams/`.
7. Keep business logic out of CLI scripts.

## Requirement Analyzer

The analyzer converts natural-language requirements into a validated Diagram.
Extract only stated information. Do not invent systems, protocols, databases,
technologies, or relationships. Prefer omission over invention; retain generic
terms and distinct components unless the requirement clearly equates them. If
the text cannot support a valid model, fail rather than fabricate one. The
contract is in `src/diagram_generator/analyzer_contract.py`; extraction rules
are in `prompts/requirement_analyzer.md`.

## Diagram Planner

The planner selects presentation views from a validated model. The full model
remains the source of truth. A view may filter nodes and existing edges,
choose direction, and group selected nodes, but must not add architecture
facts or communication edges. Follow `prompts/diagram_planner.md`.

## Testing

Use pytest for Python tests. Render with the repository's local official
Mermaid CLI and verify the SVG output.
