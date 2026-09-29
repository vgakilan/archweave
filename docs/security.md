# Security and publication

## Requirement and diagram data

Requirements can contain confidential business processes, interfaces, system
names, and deployment details. Do not commit requirement documents without
explicit approval. The repository contains local example requirements,
including a PDF and extracted text; review each file before any future GitHub
publication. Generated JSON models, Mermaid files, and SVGs can reveal the
same architecture details, so review them as well. `.gitignore` keeps ordinary
private requirement files out of `git add --all` by default, while retaining
the two small approved-style text fixtures as candidates for review.

Do not commit credentials, `.env` files, API keys, or tokens. Use environment
variables for secrets. The OpenAI API analyzer is optional; the normal Codex
workflow and test suite do not require `OPENAI_API_KEY`. Decide whether a
requirement may be sent to any external service before using that optional
integration. No API call is made by the deterministic model, planner, or
renderer pipeline.

## Mermaid and npm advisories

As checked on 2026-09-29, `npm audit --json` reports **six high-severity
package findings** in the local Mermaid CLI tree. The root direct dev
dependency is `@mermaid-js/mermaid-cli@12.0.0`; the findings propagate through
`mermaid@12.0.0`, `chevrotain@11.1.2`, `@chevrotain/gast@11.1.2`, and
`@chevrotain/cst-dts-gen@11.1.2` to transitive `lodash-es@4.17.23`.
The underlying high advisory is
[code injection through `_.template` imports keys](https://github.com/advisories/GHSA-r5fr-rjxr-66jc);
the audit also lists a
[prototype-pollution advisory](https://github.com/advisories/GHSA-f23m-r3pf-42rh)
for `lodash-es`. The registry reports a possible remediation by moving the
CLI to `11.17.0`, which is a major-version change from the installed CLI.
No dependency change or `npm audit fix` was made as part of this cleanup.

The intended use is local CLI rendering, not a network-exposed Mermaid
service. That narrows remote exposure, but it does not prove untrusted Mermaid
input harmless: CLI rendering still processes model-derived content in a
local browser process. Review and refresh the audit before publishing or
processing untrusted requirements at scale. Keep npm dependencies local;
do not install the CLI globally.
