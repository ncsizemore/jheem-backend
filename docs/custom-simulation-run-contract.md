# Custom-simulation run contract

This document defines the identity and lifecycle shared by `jheem-backend` and
`jheem-portal` for on-demand simulations.

## Version 1 identity

The backend remains the authority for parameter definitions and scenario-key
derivation. For a configured model, allowed location, and normalized parameters:

```text
scenario_key = the configured cacheKeyPrefix (when present), followed by each
               configured parameter keyPrefix and normalized integer value
request_id   = v1:<backend_model_id>:<location>:<scenario_key>
run_title    = custom-sim: <request_id>
```

Example:

```text
v1:ryan-white-msa:C.12580:a50-o30-r40
```

`request_id` is an optional `workflow_dispatch` input during the compatibility
window. When supplied, the workflow MUST recompute the expected identity and
fail before simulation if the values differ. Calls from legacy clients that omit
the input continue to run; the workflow derives the same effective identity for
result metadata.

## Lifecycle invariants

1. A cache hit is complete only when the published CloudFront object is readable.
2. A cache miss may be looked up without launching compute. Only an explicit user
   launch action may dispatch a new workflow.
3. Active-run deduplication and status recovery use exact `run_title` equality.
   A location substring is never a run identity.
4. A supplied GitHub run ID is trusted only after its title exactly matches the
   expected request title.
5. Workflow concurrency groups identical request IDs with
   `cancel-in-progress: false`, so the first run completes and later duplicate
   dispatches wait rather than replacing it. Before compute, the serialized run
   checks S3 and skips simulation when its predecessor already published the
   deterministic object.
6. Successful workflow completion is not equivalent to publication. The portal
   reports a short finalizing state until CloudFront serves the object.

## Compatibility and deployment order

Deploy in this order:

1. **Backend:** add the optional input, validation, concurrency, title, and
   metadata. Existing portal dispatches still work.
2. **Portal:** send `request_id`, require explicit `action: "launch"`, use exact
   identity matching, validate direct run IDs, and rate-limit cache-miss launches.
3. **Observe:** allow legacy in-flight runs to finish. New portal requests do not
   depend on legacy title matching.

Rollback is also ordered: roll the portal back before removing backend support.
The backend input should remain optional until all deployed portal revisions that
omit it are no longer expected to make requests.

## Versioning

Any change that makes an existing identity refer to different scientific inputs
or cache semantics requires a new contract prefix (`v2`, etc.) or a new scenario
cache-key prefix. A version bump must be deployed backend-first using the same
compatibility sequence.
