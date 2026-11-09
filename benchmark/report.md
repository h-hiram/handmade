# Benchmark results

| Request | Hostile | Condition | Score | Gate |
|---|---|---|---|---|
| clinic-dashboard | no | handmade | 100 | PASS |
| sacco-signup | no | handmade | 100 | PASS |
| coffee-landing-hostile | yes | plain | 48 | FAIL |
| coffee-landing-hostile | yes | handmade | 100 | PASS |

| Condition | Runs | Mean score | Gate pass rate |
|---|---|---|---|
| plain | 1 | 48 | 0% |
| handmade | 3 | 100 | 100% |
