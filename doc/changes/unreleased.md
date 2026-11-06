# Unreleased

## Summary

This update drops support for Python 3.10, updates the Exasol Toolbox and project dependencies, and removes UDF debug output forwarding. It also includes dependency security updates and a lockfile refresh.

## Security

 - #76: Updated dependencies
 - #77: Updated dependencies on top of 0.6.1
 - #80: Updated dependencies
 - #83: Updated poetry dependencies
 - #88: Updated poetry dependencies
 - #95: Updated poetry dependencies, exasol-integration-test-docker-environment (3.4.0 -> 5.0.0)
 - #98: Resolved vulnerabilities on 0.6.1
 - #101: Added exasol-toolbox as a development dependency

## Refactoring

- #80: Updated to poetry 2.1.2
- #87: Fixed variable name
- #117: Updated `exasol-toolbox` to 10.0.0
- #119: Updated `exasol-toolbox` to 10.2.0 and re-enabled `check-workflows` in `checks.yml`
- #138: Removed support for Python 3.10 and update exasol-toolbox to 12.0.0
- #139: Removed UDF debug output forwarding

## Internal

 - Relocked to fix security vulnerabilities
