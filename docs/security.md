# Security and publication

## Requirement and diagram data

Requirements can contain confidential business processes, interfaces, system
names, and deployment details. Do not commit requirement documents without
explicit approval. Generated JSON models, Mermaid files, SVGs, and reports can
reveal the same details. `.gitignore` excludes `requirements/` and `diagrams/`
by default; review any artifact before sharing or force-adding it.

Do not commit credentials, `.env` files, API keys, or tokens. The deterministic
model validator and renderer do not call an external analysis API. The
single-command workflow invokes the signed-in Codex CLI twice and sends the
parsed Markdown for analysis and planning. Review the requirement's sharing
rules before running it.

AnyDoc converts supported documents locally by default. The parser's optional
`--ocr hosted` mode sends a scanned PDF to Firecrawl Parse. Review that choice
for confidential requirements. Parsed Markdown under `requirements/parsed/`
is ignored by Git by default and may contain the full source text.

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
This cleanup removed unused icon packages. It did not change the Mermaid CLI
version or run `npm audit fix`.

The intended use is local CLI rendering, not a network-exposed Mermaid
service. That narrows remote exposure, but it does not prove untrusted Mermaid
input harmless: CLI rendering still processes model-derived content in a
local browser process. Review and refresh the audit before publishing or
processing untrusted requirements at scale. Keep npm dependencies local;
do not install the CLI globally.
