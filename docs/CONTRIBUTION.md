# Contribution Guide

## Branch Strategy

- `master` is protected.
- Direct pushes to `master` are disallowed by branch protection.
- All changes merge through pull requests.

## Local Quality Gates

Install runtime and quality-gate tooling:

```bash
make install-runtime
```

This installs both `pre-commit` and `pre-push` hooks:

- `pre-commit`: lightweight hygiene hooks only.
- `pre-push`: runs `make quality` and blocks push on failure.

Install heavy ML/train dependencies only when needed:

```bash
make install-train
```

## Tests

Fast/unit tests (default local quality flow):

```bash
make test-fast
```

Integration tests (intentional run only):

```bash
make test-integration
```

Quality command (used by pre-push and PR checks):

```bash
make quality
```

Lightweight quality command (format + lint + type-check only):

`make quality` runs format check + lint + type-check + `test-fast` only.
Integration tests are intentionally excluded from local pre-push.

## PR And Merge Expectations

1. Create a branch from `master`.
2. Run `make quality` locally (or rely on `pre-push`).
3. Open PR to `master`.
4. Wait for `Quality Gates` and `Integration Tests` checks to pass.
5. Merge after checks pass.

Self-merge can be enabled while still requiring status checks.

## Branch Protection (Automated Via GitHub CLI)

Apply branch protection for `master`:

```bash
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  /repos/secsuite/fake-news-api/branches/master/protection \
  -f required_status_checks.strict=true \
  -f required_status_checks.contexts[]="Quality Gates" \
  -f required_pull_request_reviews.required_approving_review_count=0 \
  -f enforce_admins=true \
  -f restrictions=
```

This enforces:

- PR required before merge.
- `Quality Gates` required.
- No direct pushes.
- Policy applies to admins.
