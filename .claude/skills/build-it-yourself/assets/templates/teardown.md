# Teardown: <project or app name>

- **Target:** <repo URL @ commit>  |  <app name, version, platform, where the artifact came from>
- **Type:** source repository | shipped app (<Electron / Android / iOS / native / CLI / web / game>)
- **Licence / terms:** <licence, and what it means for republishing the rebuild>
- **Date analysed:** <YYYY-MM-DD>   **Scope:** <whole thing / which slice>

Evidence labels (shipped apps): **[E]** evidence (cite path:line, file, REA finding or URL) · **[I]** inference (give the reasoning) · **[?]** unknown

## 1. Origin and purpose
Why it exists, who it's for, what it replaced, the author's philosophy (cite the README, first commits, blog posts).

## 2. Stack
| Layer | Technology (version) | Source of evidence |
|---|---|---|

## 3. Architecture
```mermaid
flowchart LR
  %% deployables / processes, modules, external services
```
One paragraph per component: its responsibility, where it lives, what it talks to.

## 4. Key flows
### Flow: <user action>
```mermaid
sequenceDiagram
```
Step-by-step trace with citations.

## 5. Data model and storage
```mermaid
erDiagram
```
Where data lives (DB, files, local storage, cloud), constraints, migrations, sync.

## 6. Techniques worth learning
| Technique | Where | Why they did it | Skill-map node |
|---|---|---|---|

## 7. How it was built (archaeology / feature history)
First commit or first version, the order features arrived in, rewrites and what triggered them.

## 8. Weaknesses and what we'd do differently

## 9. Unknowns (shipped apps)
Each one becomes a design decision the learner makes.

## Sources
