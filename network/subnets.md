# Network Subnet Plan

Parent CIDR: 10.20.0.0/16

| Subnet | CIDR | Usable Hosts | Required Hosts | Purpose |
|---|---|---:|---:|---|
| App | 10.20.0.0/22 | 1022 | 1000 | Application workloads |
| Public | 10.20.4.0/24 | 254 | 250 | Public-facing services |
| Data | 10.20.5.0/25 | 126 | 100 | SeaweedFS and data services |
| Management | 10.20.5.128/27 | 30 | 20 | Cluster administration |

## Design Notes

- The parent network is 10.20.0.0/16.
- Subnets use non-overlapping CIDR ranges.
- Each subnet has enough usable IPv4 addresses for its requirement.
- App workloads are isolated from data services using network access rules.
- Public services use a separate subnet.
- Management resources use a smaller dedicated subnet.
