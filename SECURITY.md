# Security Policy

## Supported versions

lodekit is pre-alpha. Only the latest release of each package receives security fixes.

| Package | Supported |
|---|---|
| latest `0.x` release of each `lodekit-*` package | yes |
| older releases | no |

## Reporting a vulnerability

**Please do not report security vulnerabilities through public issues, discussions or pull
requests.**

Use GitHub's private vulnerability reporting instead:

1. Open the repository's [Security tab](https://github.com/nakicam/lodekit/security).
2. Click **Report a vulnerability** and fill in the advisory form.

Please include:

- the affected package(s) and version(s),
- a description of the issue and its impact,
- steps to reproduce or a proof of concept,
- any known mitigations.

## What to expect

- We aim to acknowledge reports within 7 days.
- We will keep you informed about the assessment and the fix.
- Once a fix is released we publish a GitHub Security Advisory and credit you unless you prefer
  to stay anonymous.

lodekit is maintained in spare time; response times are best effort.

## Scope notes

- Never put secrets (API keys, database passwords, S3 credentials) into configuration files,
  prompts, SQL or example code. lodekit reads secrets only from the environment or a secret store.
- Vulnerabilities in upstream projects (e.g. DuckDB, LangGraph, dlt, dbt) should be reported to
  those projects. Tell us as well if lodekit's usage makes them exploitable.
