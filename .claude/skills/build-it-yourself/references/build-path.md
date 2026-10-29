# The build path

The build path turns the teardown or design into **milestones the learner builds alone**, each preceded by the learning it needs, and ending in a **shipped product**. It lives in `build-path.md`; each milestone uses `assets/templates/milestone.md`.

## Principles

- **Walking skeleton first.** Milestone 1 is the thinnest end-to-end slice that runs and is deployed or packaged: a window that opens, an endpoint that answers, a CLI that prints its version, built by CI. Shipping is wired in from the start, then refined at the end.
- **Vertical slices.** Each milestone delivers one user-visible capability through every layer. Avoid "do the whole database layer" milestones.
- **The author's order, simplified.** In reverse mode, follow the order the original was built in (git archaeology, or the feature history for shipped apps), skipping the detours.
- **One new hard thing per milestone.** If a milestone needs three unknown core skills, split it.
- **Sized to finish.** Most milestones take 2–10 hours of the learner's time. Estimate, then adjust from what actually happened (record it in `log.md`).
- **Tests define done.** Every milestone has acceptance criteria and test cases. Give test cases as **separate copyable code blocks** (input, then expected output), not tables, so each value can be copied on its own.

## Milestone anatomy (`assets/templates/milestone.md`)

1. **Goal**: one sentence, user-visible.
2. **Why now**: what it unlocks, and what the original did at this stage (reverse mode).
3. **Skills needed**: skill-map IDs. Unknown ones are taught first, with mastery-coach.
4. **Spec**: behaviour, interfaces, constraints, and non-goals for this milestone. Interfaces are given in words and as signatures with empty bodies, never as implementations (the brief in `framework/rules/hands-on-coding.md`).
5. **Acceptance criteria and test cases**: the copyable blocks. For UI, a scripted manual checklist.
6. **Hints available**: the stuck-protocol ladder, prepared in advance but revealed one rung at a time.
7. **Stretch goals**: for the learner who finishes early.
8. **Compare with the original** (after building only): file and line references for repos; behaviour and REA evidence for shipped apps.
9. **Review questions**: 3–5 interview-grade questions about the decisions made in this milestone, plus recall from earlier ones.

## Loop per milestone

```
teach the unknown skills (mastery-coach) → brief → learner builds → tests pass → code review
   → "explain your code" → compare with original → recall questions → log → next milestone
```

## Shipping milestones (always last, and seeded in milestone 1)

Real software is installable, updatable and trustworthy. Plan the shipping milestones for the target platform, and verify current tools and store rules with a search, since they change often.

| Target | What "shipped" means | Skills to put in the skill map |
|---|---|---|
| **Web app / API** | Deployed on a real domain with HTTPS, migrations run in CI, rollback possible | containers, a host (VPS, PaaS or serverless), DNS and TLS, environment config and secrets, CI/CD, DB migrations in deploys, logs, metrics and health checks, backups |
| **Desktop: Electron** | Signed installers for each OS, auto-update, crash reporting | a packager (Electron Forge or electron-builder), code signing (Windows Authenticode; macOS Developer ID plus notarization), an auto-update feed, Electron security hardening (context isolation, sandboxing, fuses, CSP) |
| **Desktop: Tauri** | Signed bundles, updater | the Tauri bundler, signing, the updater plugin and its signing keys, the allowlist and capabilities model |
| **Desktop: native** | Installers or packages for each OS | the platform toolchain, MSI/MSIX, `.dmg`/`.pkg`, AppImage/Flatpak/`.deb`, signing |
| **Android** | A signed release on a store or F-Droid, or an installable APK | the release build, shrinking and obfuscation (R8), signing keys and Play App Signing, the AAB format, store listing and policies, staged rollout, crash and ANR monitoring |
| **iOS** | TestFlight, then the App Store | certificates and provisioning, archiving, TestFlight, review guidelines, privacy manifest |
| **Flutter / React Native** | Both mobile stores (plus desktop or web if targeted) | each platform's release pipeline, flavours and environments, over-the-air update limits |
| **CLI** | One-line install on each OS | cross-compilation, release archives, checksums and signatures, a release tool (for example GoReleaser or cargo-dist), Homebrew/Scoop/winget/npm/PyPI/crates.io publishing, `--version` and shell completions |
| **Library / package** | Published, versioned, documented | semver, changelogs, the registry publish flow, API docs, CI matrices |
| **Game** | A playable build on a storefront or itch.io | engine export templates, platform builds, asset pipelines, storefront upload tools |

Shipping milestones follow the same rules: the learner writes the pipeline, the config and the signing steps. You teach the concepts (what notarization proves, why the keys must never be in the repo, how an update feed is verified) and review what they wrote.

## Pacing and adjustment

- After each milestone, compare the estimate with the actual time, check how recall is going, and note what the learner found hard. Resize the next milestone to match.
- If a milestone stalls for more than two sessions, split it, or add a short learning detour.
- Keep a visible checklist of the path in `build-path.md`, so a returning learner sees at once where they are.
