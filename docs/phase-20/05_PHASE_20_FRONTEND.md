# Phase 20 — Frontend Specification

Phase 20 is primarily an operational/deployment foundation.

## Default
No frontend feature is required merely to represent cloud deployment.

## If Backend Health/Readiness Is Added
Only if repository inspection establishes a genuine operational need:
- keep it read-only;
- do not expose secrets, database URLs, credentials, filesystem paths, or internal connection details;
- expose only a minimal application readiness state;
- do not add destructive controls;
- preserve existing global error handling.

## Otherwise
Leave the frontend untouched and run its regression gates.

No UI for cloud credentials, database migration, backup upload, restore, arbitrary command execution, or infrastructure provisioning.
