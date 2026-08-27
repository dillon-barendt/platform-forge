# Platform Forge Contributor Guidance

Platform Forge is a typed Python 3.13 CLI for deterministic platform scaffolding and narrowly scoped GitHub governance.
Keep changes small, explicit, and consistent with the existing package and template contracts.

## Repository Map

- `src/platform_forge/`: CLI, command handlers, configuration, generation, and GitHub-governance implementation.
- `src/platform_forge/templates/cookiecutters/`: rendered project templates. Treat these as a public scaffold contract.
- `tests/`: pytest coverage for CLI, configuration, generators, templates, and GitHub reconciliation.
- `docs/`: MkDocs documentation and ADRs.

## Implementation Rules

- Target Python 3.13 and preserve strict mypy compatibility.
- Use explicit types and keep public CLI/configuration behavior deterministic.
- Preserve package boundaries; avoid speculative abstractions and unrelated refactors.
- Add or update focused tests for behavior changes. Template changes also need a rendered-project smoke test when
  applicable.
- Keep CLI help, README/docs, changelog, and release metadata aligned when a user-visible command, package identity, or
  release workflow changes.
- Do not edit generated output directories, virtual environments, or unrelated working-tree changes.

## GitHub Governance Safety

- `platform-forge github plan` is read-only and should be used to preview configuration changes.
- `platform-forge github apply --yes` mutates remote GitHub state. Run it only after the user has reviewed the plan and
  explicitly approved the mutation.
- Keep reconciliation upsert-only: do not delete unmanaged remote resources.
- After an approved apply, rerun `platform-forge github plan --check` to verify convergence.

## Validation

Run the narrowest relevant checks first, then the full applicable set:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
uv run --group docs mkdocs build
```

Report commands actually run and distinguish project failures from unrelated workspace state or unavailable external
credentials.
