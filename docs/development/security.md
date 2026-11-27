# Security baseline

lodekit is a public repository. This page lists the repository hardening required by M0, how to
apply each setting, and how to verify it. Report vulnerabilities as described in
[SECURITY.md](https://github.com/nakicam/lodekit/blob/main/SECURITY.md).

| Control | Where | Status check |
|---|---|---|
| Secret scanning + push protection | Repository settings | `gh api repos/nakicam/lodekit --jq .security_and_analysis` |
| gitleaks on every PR | `secrets` job in [CI](ci.md) | part of `CI success` |
| CodeQL (Python + GitHub Actions) | [`.github/workflows/codeql.yml`](https://github.com/nakicam/lodekit/blob/main/.github/workflows/codeql.yml) | Security → Code scanning |
| Dependabot alerts, security updates, weekly grouped version updates | [`.github/dependabot.yml`](https://github.com/nakicam/lodekit/blob/main/.github/dependabot.yml) | Insights → Dependency graph → Dependabot |
| Private vulnerability reporting | Repository settings | Security → Advisories → "Report a vulnerability" |
| Branch protection on `main` | Repository settings | `gh api repos/nakicam/lodekit/branches/main/protection` |
| Licence policy (ADR-000) | `licenses` job in [CI](ci.md) | part of `CI success` |
| Least-privilege workflows | `permissions: contents: read` by default; publishing only from the protected `testpypi` environment via OIDC | review |

## Applying the repository settings

The settings need admin rights on `nakicam/lodekit`. Run these commands with the **personal**
github.com account. In PowerShell, clear a company token first:

```powershell
$env:GH_TOKEN = $null; $env:GH_HOST = 'github.com'
gh auth status   # must show the nakicam account on github.com
```

```console
# Secret scanning, push protection and Dependabot security updates
gh api -X PATCH repos/nakicam/lodekit --input - <<'EOF'
{"security_and_analysis": {
  "secret_scanning": {"status": "enabled"},
  "secret_scanning_push_protection": {"status": "enabled"},
  "dependabot_security_updates": {"status": "enabled"}
}}
EOF

# Dependabot alerts and private vulnerability reporting
gh api -X PUT repos/nakicam/lodekit/vulnerability-alerts
gh api -X PUT repos/nakicam/lodekit/private-vulnerability-reporting
```

### Branch protection for `main`

Branch protection requires a pull request and a green `CI success` check (see
[required status check](ci.md#required-status-check)). Enable it **after** the CI workflow is on
`main`. Otherwise the required check never reports, and the M0 bootstrap PRs cannot be merged.

```console
gh api -X PUT repos/nakicam/lodekit/branches/main/protection --input - <<'EOF'
{
  "required_status_checks": {"strict": true, "contexts": ["CI success"]},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 0, "dismiss_stale_reviews": true},
  "restrictions": null,
  "required_linear_history": true,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

With a single maintainer, `required_approving_review_count` is 0, because GitHub does not let
authors approve their own PRs. The PR requirement still forces every change through CI. Raise it
to 1 once there is a second maintainer.

### DCO

Install the [DCO GitHub App](https://github.com/apps/dco) for the repository. Then add `DCO` to the
required status checks.

Dependabot commits are not signed off. Either allow the DCO app's "Set DCO to pass" remediation for
`dependabot[bot]` PRs, or add a sign-off commit before merging.

## Verification

```console
gh api repos/nakicam/lodekit --jq .security_and_analysis
gh api repos/nakicam/lodekit/branches/main/protection --jq '{checks: .required_status_checks.contexts, linear: .required_linear_history.enabled}'
gh api repos/nakicam/lodekit/private-vulnerability-reporting --jq .enabled
```
