# Cart service: connection pooling rollout

CHK-105, load test at 2,000 req/s, before vs after.

## Latency

```compare
title: Checkout API under load
lower: yes
p50 latency | 180ms | 142ms
p95 latency | 530ms | 412ms
p99 latency | 1,240ms | 1,310ms
Throughput | 1,850 req/s | 2,140 req/s | higher
```

## Quality

```compare
Test coverage | 74% | 78%
Conversion rate | 3.1% | 3.0%
Error rate | 0.42% | 0.11% | lower
Open bugs | 12 | 12
```

The p99 regression is from cold pool starts after deploys; CHK-107 tracks a warm-up step.
