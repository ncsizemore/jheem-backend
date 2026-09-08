# Calibration delivery

The manual **Promote calibration release** workflow delivers the reviewed public Ryan White
calibration release through the existing portal S3 bucket and CloudFront distribution.
`.github/config/calibration-promotion.json` pins the merged portal consumer commit, release,
generated index digest, destination, and exact file count and byte total. The consumer verifies
the GitHub release metadata, assets, and scientific artifact contracts before any AWS operation.

## Preview and publish

Run the default preview from the backend default branch:

```sh
gh workflow run promote-calibration.yml --repo ncsizemore/jheem-backend --ref master -f mode=plan
```

Preview downloads 12,352,175 bytes of public release assets and stages 158 files totaling
89,689,757 bytes (85.5 MiB). It uses no AWS credentials and makes no AWS requests. The job summary
and the `calibration-delivery-receipt` artifact contain the proposed destination, exact file
inventory, hashes, byte counts, and three product manifest URLs and hashes.

To publish the reviewed plan:

```sh
gh workflow run promote-calibration.yml --repo ncsizemore/jheem-backend --ref master -f mode=promote
```

Publication repeats source verification, then uses the backend's existing AWS publisher
credentials. It is limited to:

- S3: `s3://jheem-data-production/portal/calibration/ryan-white-calibration-v1.0.0/`;
- CloudFront: `https://d320iym4dtm9lj.cloudfront.net/calibration/ryan-white-calibration-v1.0.0/`.

The workflow serializes delivery runs, permits execution only from `master`, and has a 20-minute
timeout. The first publication performs one prefix listing, up to 158 conditional PUTs, and
checksum HEAD checks. It verifies every file via CloudFront using the portal Origin header and
checks CORS, media type, cache policy, and the SHA-256 of the delivered bytes. Each object uses
`Cache-Control: public, max-age=31536000, immutable`. Objects preserve the extracted release bytes;
JSON is served as `application/json`, checksums as `text/plain`.

The new storage footprint is 89.7 MB. A complete delivery verification reads that same amount
before any CDN compression. There is no model computation, new infrastructure, scheduled job,
or CloudFront invalidation. Only the small plan and completion receipt are retained as GitHub
Actions artifacts, for 14 days; the expanded release stays on the temporary runner disk.

## Failure and retry behavior

Every write uses S3 `If-None-Match: *` and the expected SHA-256 checksum. This is an atomic
create-only operation, including if another writer races the preflight check; see the
[AWS PutObject reference](https://docs.aws.amazon.com/cli/latest/reference/s3api/put-object.html).
This workflow enforces non-overwrite behavior; it does not enable bucket-level Object Lock or
restrict other administrators' credentials.

Before writing, the workflow checks every existing object in the release prefix. An unexpected
object, different checksum, length, or delivery metadata stops the run. Matching objects from a
partial run are reused and reverified, so an interrupted delivery can be resumed with the same
command. The workflow never deletes an object, replaces a different object, or automatically
changes an access policy. Permission and CORS failures require inspecting the existing delivery
configuration before rerunning.

The generated root `index.json` is uploaded last, after all other files pass CloudFront
verification. If the index already exists but files are missing, the workflow stops. A rerun of
a complete matching release verifies it without writes. If the final index delivery check fails,
the run still fails and emits no successful completion receipt; the presence of an index alone
is not sufficient evidence of completed delivery. A cached CloudFront error may require waiting
for its existing TTL before a retry.

## Acceptance and next step

The local real-release preview reproduced the pinned index
`0f6edcbba221656c58eef1542b033e4b3b621adcf5bf36e5ff39d98c192bb20e`, all 158 files, and
89,689,757 bytes. Unit tests exercise interrupted/resumed publication, conflicting objects,
conditional-write races, index ordering, CORS, corrupted delivery, and local-file changes.
The existing CloudFront route was also checked with the portal Origin and permits that origin.
Backend CI repeats the real preview on Linux with the pinned consumer and no AWS credentials,
so the PR checks include the release downloads and platform-specific extraction behavior. This
adds the small public release download to backend validation and requires GitHub release
availability; it does not run a posterior build.

Cloud publication remains to be executed through the merged workflow. After a successful
promotion receipt, verify the published manifest URLs and add their pins to backend model
configuration. That subsequent unit enables the portal to build its calibration presentation
against the promoted release. Future releases receive new prefixes. Rollback selects a prior
release in model configuration.
