# Current limitations

- The one-command workflow requires an installed, signed-in Codex CLI. It
  sends the parsed Markdown for model interpretation and view selection.
- Model interpretation is probabilistic. Python validates structure, evidence
  excerpts, and references; it cannot guarantee every source fact was captured.
- Validation confirms that evidence excerpts occur in the Markdown, but a
  human still needs to review whether each excerpt supports the asserted fact.
- The supported views are architecture, flowchart, and sequence. Other UML
  notations require additional model facts and renderers.
- View plans are Codex-authored JSON. The validator checks their references and
  scope, but it does not score visual clarity; inspect the rendered SVGs.
- AnyDoc's local parser cannot OCR scanned PDFs. Optional hosted OCR sends the
  document to Firecrawl Parse.
- Mermaid layout can be awkward for disconnected or crowded graphs. Split
  views rather than add unsupported links for layout.
- There is no draw.io export or organization-specific publication workflow.
