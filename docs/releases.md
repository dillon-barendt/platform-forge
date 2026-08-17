# Release Process

Platform Forge uses Release Please with Conventional Commits. Direct release commits are not pushed through the
default-branch ruleset.

## Repository setup

Run the initializer from a Python repository root:

```bash
platform-forge github init-release
```

Review and commit the generated workflow, manifest, configuration, and version annotation. Add the repository to the
governance file's `[release].repositories` list and apply governance so GitHub Actions may open the release pull
request. Apply enables selected-repository Actions access where needed, keeps the organization token default read-only,
and opts only release repositories into pull-request creation. The workflow requests only its declared `contents`,
`issues`, and `pull-requests` permissions.

## Creating a release

1. Merge changes to the configured release branch using Conventional Commit titles.
2. `fix:` changes propose a patch; `feat:` changes propose a minor; a `!` or `BREAKING CHANGE` proposes a major.
3. Release Please creates or updates one release pull request containing the version and changelog changes.
4. Review and merge that pull request through the normal branch ruleset.
5. Release Please creates the SemVer Git tag and GitHub Release from the merged commit.

Platform Forge does not publish to PyPI, configure package-manager credentials, or bypass branch protection in this
MVP. A failed release remains visible in GitHub Actions and can be rerun after correcting the repository or enterprise
policy.
