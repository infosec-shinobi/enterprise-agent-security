# ADR-002 — Manifest-driven lab discovery

Status: Accepted; B02 validated on Windows.

## Context
Lab 01 has a validated v1 YAML manifest and canonical control IDs. Labs 02/03 have manual scaffolds but discovery requires a valid manifest. A hardcoded frontend catalog would drift from the runnable definitions.

## Decision
Discover only direct children of the server-owned labs directory with manifest.yaml and README.md. Reuse tools.validate_manifest.load_manifest, join canonical control details, expose typed read-only list/detail API responses. Rescan on request, exclude invalid entries and all valid entries sharing a duplicate ID. Return fixed diagnostic reasons rather than raw parser errors. Reject linked paths and oversized manifests. Treat IDs as lookup keys, never filesystem paths. Render metadata as React text, not HTML. No script execution, dynamic imports, manual rendering or service probes.

## Alternatives
Hardcoded UI lists are simpler initially but duplicate metadata. A database index enables larger catalogs but adds synchronization and migration complexity. Recursive discovery broadens scope unnecessarily. Static build-time generation requires rebuilds for new labs.

## Consequences
New valid manifests appear on refresh without frontend changes. Invalid manifests remain visible as diagnostics; missing manifests are intentionally absent. Local repository files are trusted administrative inputs, not a hostile upload interface; filesystem checks are not race-proof against a concurrent local writer. No caching or file watcher yet. A valid manifest does not establish runner support, service availability, actual control effectiveness or framework compliance. Future mappings retain canonical IDs; execution must separately enforce trusted adapters.

## Validation
User confirmed dynamic discovery and removal without frontend changes, duplicate-ID exclusion and diagnostics, API and UI failure/recovery, backend regression tests and frontend build. No application changes were needed for the Windows CRLF fixture issue. Linux/macOS validation remains outstanding.
