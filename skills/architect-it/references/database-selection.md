# Database Selection Reference

## PACELC model

PACELC extends CAP by also reasoning about the latency–consistency tradeoff when the system is running normally (no partition).

```
If Partition (P):
    choose Availability (A)  →  PA system: stay up, accept stale reads
    choose Consistency (C)   →  PC system: refuse requests rather than serve stale data

Else (E), no partition:
    choose Latency (L)       →  EL system: fast responses, eventual consistency
    choose Consistency (C)   →  EC system: slower responses, always-consistent reads
```

A database's PACELC class (e.g., PA/EL) tells you its behaviour under both failure and normal operation.

## Classification table

| Database | PACELC class | Data model | Strong consistency | Tunable | Typical use case |
|---|---|---|---|---|---|
| PostgreSQL | PC/EC | Relational | Yes | No | Transactional apps, financial records, any join-heavy workload |
| MySQL / MariaDB | PC/EC | Relational | Yes (InnoDB) | No | Web apps, CMSs, read-heavy OLTP |
| CockroachDB | PC/EC | Relational (distributed) | Yes | No | Geo-distributed OLTP requiring SQL semantics |
| MongoDB | PA/EL | Document | No (default) | Yes | Flexible-schema content, catalogs, user profiles |
| Cassandra | PA/EL | Wide-column | No (default) | Yes | High-write time-series, event logs, IoT, geo-distributed |
| DynamoDB | PA/EL | Key-value / document | No (default) | Yes (via transactions) | Serverless, variable traffic, single-table access patterns |
| Redis | PA/EL | Key-value / structures | No | No | Cache, session store, rate limiting, pub/sub |
| Kafka | PA/EL | Append-only log | No (offset lag) | No | Event streaming, CDC, async decoupling between services |
| ClickHouse | PC/EL | Columnar | Yes (within shard) | Partial | OLAP, analytics, aggregations over large datasets |
| Neo4j | PC/EC | Graph | Yes | No | Relationship-heavy queries: social graphs, fraud detection, knowledge graphs |
| S3 / object store | PA/EL | Blob / object | No (eventual) | No | Large binary data, model artifacts, data lake raw layer |

## Decision tree

```
Need ACID transactions or complex joins?
├── Yes → relational
│   ├── Single-region?       → PostgreSQL / MySQL
│   └── Multi-region?        → CockroachDB
└── No
    ├── Write throughput > read throughput, or geo-distributed writes?
    │   ├── Time-series / append-only?  → Cassandra
    │   └── Variable schema / documents? → DynamoDB (serverless) | MongoDB (self-hosted)
    ├── Sub-millisecond latency required?
    │   └── Yes → Redis (cache / session)
    ├── Graph traversal (≥3 hops)?
    │   └── Yes → Neo4j
    ├── Analytical aggregations over large datasets?
    │   └── Yes → ClickHouse
    ├── Event streaming / async decoupling?
    │   └── Yes → Kafka
    └── Large binary objects or data lake?
        └── Yes → S3 / object store
```

## Polyglot persistence heuristics

Combining databases is often correct — but only introduce a second store when there is a concrete reason.

| Pattern | When to use |
|---|---|
| PostgreSQL + Redis | PostgreSQL is the system of record; Redis caches hot reads or stores sessions. Add Redis only when query latency is a stated requirement. |
| Cassandra + Kafka | Cassandra persists event state; Kafka delivers the stream. Use when consumers need both replay (Kafka) and point-in-time lookup (Cassandra). |
| PostgreSQL + S3 | PostgreSQL stores metadata and references; S3 stores raw files or model artifacts. |
| DynamoDB + ElasticSearch / OpenSearch | DynamoDB for primary access patterns; search index for full-text or faceted queries. Add only when full-text search is an explicit requirement. |
| OLTP + ClickHouse | Write to the operational DB; replicate to ClickHouse via CDC (Kafka/Debezium) for analytics. |

**Rule**: every additional store adds operational complexity. Justify each one with a requirement the primary store cannot meet.
