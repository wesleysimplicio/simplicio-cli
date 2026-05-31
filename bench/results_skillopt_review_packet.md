# SkillOpt Human Review Packet

pending human-review packet for SkillOpt-generated skills; this artifact intentionally does not count as approval evidence until a human fills reviewer and approved fields

## Summary

- review gated skills: 0
- pending reviews: 0
- human review complete: False
- release ready: False
- minimum reviews: 10
- minimum approval rate: 80%

## How To Complete

Fill `reviewer`, `approved`, `reviewed_at`, and `notes` in the JSON.
`approved` must be a real boolean, not a string. Then rerun the live gate
with `--skillopt-review-json`.

## Pending Reviews

| skill | path | sha256 |
| --- | --- | --- |
