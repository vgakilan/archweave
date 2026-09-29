# Current limitations

This is an internal MVP/prototype. Its current boundaries are:

- Codex is the normal requirement-analysis agent; the quality of extraction
  still depends on source clarity and human review.
- PDF extraction depends on readable text or inspectable figures. Scanned or
  poorly extracted PDFs may need separate preparation.
- Layout quality depends on Mermaid. Disconnected graphs can produce poor or
  tall layouts even when a view prefers `LR`.
- The planner currently uses predefined JSON view plans. It validates source
  references and a configured node cap, but it does not score or reject weak
  views based on visual quality or usefulness.
- The node taxonomy has no dedicated cache or coordination-service type;
  generic supported types are used only when accurate.
- There is no draw.io output, production agent framework, or CI/CD pipeline.
- An OpenAI API implementation exists but is optional; it is not required for
  the Codex workflow, deterministic pipeline, or pytest.
- There is no organization-specific governance yet for requirement retention,
  review, sharing, or publication. Teams must approve source documents and
  generated architecture artifacts before committing or distributing them.
