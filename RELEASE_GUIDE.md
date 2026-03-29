# Release guide

## Current distribution

- PyPI package name: `maxapi-sdk`
- Python import path: `maxapi`

## CI/CD setup

- `.github/workflows/tests.yml` — test and build validation;
- `.github/workflows/publish.yml` — PyPI publication and GitHub Release for tags matching `v*`.

## One-time setup

### GitHub

- host the repository on GitHub;
- ensure the release workflow has `contents: write` permission.

### PyPI

- configure a Trusted Publisher for the target GitHub repository in the `maxapi-sdk` project;
- after that, releases can be published without a long-lived API token.

## Release checklist

1. update the version in `pyproject.toml`;
2. update `README.md` and `CHANGELOG.md`;
3. run local validation:

```bash
pytest -q
python -m build
twine check dist/*
```

4. create a release commit and tag:

```bash
git add .
git commit -m "Release 0.13.0"
git tag v0.13.0
git push origin main
git push origin v0.13.0
```

5. verify the GitHub Actions run and confirm that PyPI publication and GitHub Release completed successfully.
