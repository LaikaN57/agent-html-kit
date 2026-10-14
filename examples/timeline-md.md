# Payments database migration

## Rollout plan

```timeline
title: Milestones
2026-08-04 | Kickoff | Scope agreed with Payments and SRE [done]
2026-08-25 | Schema frozen | PAY-210 [done]
2026-09-15 | Dual writes on | 100% of writes mirrored [done]
2026-10-01 | Dry-run cutover | Rolled back after 14 minutes, see below [warn]
2026-10-20 | Backfill verified | Row counts and checksums match [progress]
2026-11-03 | Cutover | Needs the change freeze lifted [blocked]
2026-11-17 | Old cluster deleted | [todo]
```

## Dry-run incident, 2026-10-01

```timeline
14:05 | Cutover started | Writes paused on the old cluster
14:09 | p95 latency at 2.4 s | Connection pool too small on the new cluster [fail]
14:12 | Rollback decided
14:19 | Writes back on the old cluster | No data lost [ok]
15:30 | Pool size raised to 200 | PAY-231 [done]
```
