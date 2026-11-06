# Task 7 - Performance Review, SLO and Error Budget

## 1. Load Test Results

Load test configuration:
- Tool: Locust 2.47.0
- Virtual users: 4
- Spawn rate: 4 users/second
- Duration: 120 seconds
- API endpoint: POST /parse
- Model version: v2

| Metric | Measured Result |
|---|---:|
| Total requests | 262 |
| Successful requests | 245 |
| Failed requests | 17 |
| Success rate | 93.51% |
| Error rate | 6.49% |
| Average latency | 1813 ms |
| p50 latency | 1700 ms |
| p95 latency | 3300 ms |
| Throughput | 2.2 requests/second |

The 17 failed requests returned HTTP 500.

## 2. Replica Distribution

| Replica | Successful Requests |
|---|---:|
| command-parser-84bdfc589d-m4wrd | 149 |
| command-parser-84bdfc589d-6pk6z | 96 |
| Total | 245 |

Both replicas successfully served requests. All successful responses used model version v2.

## 3. CPU and Memory Usage

| Pod | CPU Usage | Memory Usage |
|---|---:|---:|
| command-parser-84bdfc589d-6pk6z | 3m | 403 MiB |
| command-parser-84bdfc589d-m4wrd | 2m | 724 MiB |

These values are a kubectl top snapshot, not peak measurements.

## 4. Cold Start Measurement

Restart-to-ready time was measured over three deployment restarts.

| Run | Time |
|---|---:|
| Run 1 | 22.50 seconds |
| Run 2 | 22.43 seconds |
| Run 3 | 21.78 seconds |
| Median | 22.43 seconds |

## 5. Cost Estimation

Hypothetical rate card:
- CPU: Rs. 3.50 per vCPU-hour
- Memory: Rs. 0.45 per GiB-hour
- Two replicas, each with 1 vCPU and 1 GiB memory limit.

Hourly cost:
2 x (3.50 + 0.45) = Rs. 7.90

Estimated cost per 1000 requests:
(Rs. 7.90 / (2.2 x 3600)) x 1000 = approximately Rs. 1.00

This is a hypothetical estimate, not an actual cloud provider bill.

## 6. SLO and Error Budget

Proposed SLO targets:

| Indicator | Target | Actual | Status |
|---|---:|---:|---|
| Successful requests | >= 95% | 93.51% | Not met |
| Error rate | <= 5% | 6.49% | Not met |
| p95 latency | <= 3500 ms | 3300 ms | Met |
| Restart-to-ready | <= 30 seconds | 22.43 seconds | Met |

Error budget:
- Allowed error rate: 5%
- Actual error rate: 6.49%
- Allowed failures in 262 requests: approximately 13
- Actual failures: 17
- Error budget exceeded by approximately 4 requests.

The availability SLO was not met during this load test. The latency and restart-time targets were met.

## 7. Final Review

| Area | Finding | Limitation / Improvement |
|---|---|---|
| API performance | p95 latency was 3.3 seconds | Optimize model inference |
| Reliability | 17 HTTP 500 failures | Improve model output validity and error handling |
| Load balancing | Both replicas served requests | Test with more concurrent users |
| Resource usage | Memory usage was 403 MiB and 724 MiB | Collect continuous peak metrics |
| Cold start | Median was 22.43 seconds | Optimize model download and startup |
| Cost | Estimated Rs. 1 per 1000 requests | Compare with actual cloud pricing |
| Availability | 93.51% success rate | Reduce invalid model outputs and retest |

## 8. Limitations and Future Improvements

1. The load test used only four virtual users for two minutes.
2. The 17 HTTP 500 responses indicate that some model outputs were rejected.
3. CPU and memory values were sampled once rather than continuously.
4. Cost estimation uses hypothetical rates.
5. Future work should improve model output validity, optimize inference, and repeat load testing with higher concurrency.
