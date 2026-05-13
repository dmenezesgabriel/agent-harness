---
name: performance-scalability-audit
description: Audit software for performance, scalability, memory, concurrency, resource usage, latency, throughput, algorithmic complexity, race conditions, deadlocks, backpressure, caching, database efficiency, and operational bottlenecks.
---

## Purpose

Audit software for concrete performance and scalability risks that can reduce latency, throughput, efficiency, reliability, availability, responsiveness, or safe operation under load.

Use algorithmic analysis, resource analysis, concurrency analysis, database/query review, caching review, profiling evidence, load assumptions, queue/backpressure analysis, and production observability signals.

This playbook is language-agnostic.

## When to Use

Use when reviewing:
- slow requests
- slow UI interactions
- slow jobs or batch processing
- high memory usage
- memory leaks
- CPU hotspots
- excessive I/O
- database query performance
- N+1 queries
- cache usage
- pagination
- large data processing
- concurrency
- race conditions
- deadlocks
- concurrent updates
- async workflows
- queues and workers
- serverless cold starts
- container resource limits
- SSR/server-rendered routes
- frontend rendering performance
- API throughput
- load tests
- stress tests
- production incidents
- observability gaps
- scalability bottlenecks

Do not optimize unrelated code unless the requested change crosses those boundaries.

## Core Principle

Performance work must be tied to a concrete behavior, workload, resource, bottleneck, or risk.

Do not optimize by intuition alone.

Every finding must identify:
- operation or flow affected
- workload or scale assumption
- bottleneck or failure mode
- evidence or reasoned complexity
- user or system impact
- smallest safe remediation
- validation method

## Performance vs Scalability

Performance issue:
A single operation is slow or wasteful.

Scalability issue:
The system degrades as requests, users, tenants, data size, concurrency, workers, integrations, or events increase.

A system can be fast at small scale and fail at larger scale.

A system can scale horizontally but still have poor single-request latency.

State which problem is being reviewed.

## Review Principles

### Workload and Baseline

Identify the expected workload before judging the implementation.

Check:
- request rate
- data size
- number of users
- number of tenants
- concurrency level
- batch size
- queue depth
- payload size
- response size
- external dependency latency
- memory limits
- CPU limits
- database size
- cache size
- serverless timeout
- container limits
- browser/device constraints

Flag performance claims without workload, baseline, threshold, or measurement plan.

Key terms: workload, baseline, latency budget, throughput target, service level objective, capacity, saturation.

### Latency and Throughput

Check whether the code adds unnecessary latency or limits throughput.

Flag:
- serial work that could be safely parallelized
- unnecessary blocking calls
- excessive round trips
- chatty I/O
- unnecessary synchronous work on hot paths
- large payloads
- inefficient serialization
- repeated parsing
- repeated expensive computation
- slow startup or cold start
- excessive middleware or interceptors on hot paths

Key terms: latency, throughput, critical path, blocking call, round trip, hot path, cold start.

### Algorithmic Complexity

Check whether time and space complexity are appropriate for expected input sizes.

Flag:
- accidental O(n²) or worse behavior
- nested loops over growing data
- repeated full scans
- repeated sorting
- inefficient joins in application memory
- unbounded recursion
- inefficient string concatenation in loops
- expensive regex on untrusted or large input
- inefficient graph/tree traversal
- missing indexing or lookup structure
- processing all data when only a page/window is needed

Key terms: asymptotic complexity, time complexity, space complexity, Big O, hot path, bounded input, algorithmic efficiency.

### Memory Usage and Leaks

Check whether memory is bounded, released, and proportional to workload.

Flag:
- unbounded caches
- unbounded maps, arrays, queues, subscriptions, timers, listeners, promises, goroutines, tasks, or handles
- retaining large objects longer than needed
- loading whole files or datasets into memory
- accumulating results before streaming
- missing cleanup on component unmount, request end, job completion, or connection close
- circular references where relevant
- global mutable state retaining per-request data
- per-tenant or per-user data stored without eviction
- memory growth across repeated operations

Key terms: memory leak, retention, allocation, heap growth, garbage collection pressure, resource lifetime, bounded memory, streaming.

### Resource Lifetime and Cleanup

Check whether resources are acquired and released correctly.

Flag:
- unclosed files
- unclosed database cursors
- unclosed network connections
- leaked subscriptions
- leaked event listeners
- leaked timers
- leaked locks
- leaked semaphores
- leaked browser observers
- leaked workers
- missing cancellation
- missing finally/defer/dispose cleanup

Key terms: resource leak, cleanup, disposal, cancellation, lifetime, ownership.

### Database and Persistence Performance

Check whether data access is efficient, bounded, indexed, and transactionally safe.

Flag:
- N+1 queries
- missing indexes for filters, joins, ordering, or uniqueness
- full table scans on hot paths
- fetching too many columns
- fetching too many rows
- unbounded pagination
- offset pagination at large scale where unsuitable
- application-side joins over large data
- repeated queries inside loops
- long transactions
- lock contention
- missing batch operations
- inefficient migrations
- missing query plans for risky queries
- inconsistent transaction boundaries

Key terms: N+1 query, index, query plan, full scan, pagination, batching, transaction, lock contention.

### Caching

Check whether caching improves performance without breaking correctness.

Flag:
- missing cache on expensive repeated reads
- cache without invalidation strategy
- stale data risk
- unbounded cache
- cache stampede
- thundering herd
- caching sensitive or user-specific data incorrectly
- cache key missing tenant/user/permission dimensions
- caching errors unintentionally
- duplicate caches with inconsistent behavior
- cache hiding database inefficiency instead of fixing hot queries

Key terms: cache key, invalidation, TTL, stale data, cache stampede, thundering herd, eviction, bounded cache.

### Concurrency and Race Conditions

Check whether shared state, concurrent requests, jobs, events, and async flows are safe.

Flag:
- read-modify-write without atomicity
- concurrent updates without locking, transactions, compare-and-swap, version checks, or idempotency
- lost updates
- double processing
- duplicate submissions
- unsafe shared mutable state
- non-thread-safe objects shared across workers
- async state updates racing each other
- stale reads
- out-of-order events
- missing idempotency keys
- missing optimistic or pessimistic concurrency control
- unsafe retry behavior

Key terms: race condition, lost update, atomicity, idempotency, compare-and-swap, optimistic locking, pessimistic locking, version check.

### Deadlocks, Livelocks, and Lock Contention

Check whether locking, transactions, and synchronization can block progress.

Flag:
- inconsistent lock acquisition order
- nested locks
- long critical sections
- I/O while holding locks
- transactions held during external calls
- missing lock timeout
- retry loops without backoff
- busy waiting
- lock convoy
- starvation
- unbounded waiting
- deadlock-prone database update order

Key terms: deadlock, livelock, starvation, lock contention, critical section, timeout, backoff.

### Queues, Backpressure, and Load Shedding

Check whether producers can overwhelm consumers.

Flag:
- unbounded queues
- no backpressure
- no rate limits
- no worker concurrency limits
- no retry budget
- no dead-letter queue
- no poison-message handling
- retries amplifying load
- no load shedding
- no timeout or cancellation
- no queue depth monitoring
- no idempotency for retried jobs
- work accepted faster than it can be processed

Key terms: backpressure, queue depth, load shedding, retry storm, dead-letter queue, poison message, consumer lag.

### External Dependencies

Check whether external calls are bounded, resilient, and efficient.

Flag:
- no timeout
- no retry limit
- no exponential backoff
- no circuit breaker where needed
- no bulkhead where needed
- sequential external calls on critical path
- repeated calls for same data
- no response size limits
- no fallback for non-critical dependencies
- dependency latency hidden from observability
- external call inside transaction or lock

Key terms: timeout, retry budget, backoff, circuit breaker, bulkhead, fallback, dependency latency.

### Frontend Performance

Check whether frontend code renders efficiently and stays responsive.

Flag:
- excessive re-renders
- expensive computation during render
- large bundles
- unnecessary hydration cost
- unnecessary client-side data
- blocking main thread work
- large lists without virtualization
- layout thrashing
- unoptimized images
- unnecessary network waterfalls
- missing loading states
- memory leaks from listeners, timers, observers, subscriptions, or async effects
- stale async state updates after unmount
- inefficient state shape causing broad re-rendering

Key terms: render cost, hydration, bundle size, main thread, virtualization, layout thrashing, network waterfall, effect cleanup.

### SSR, Serverless, and Container Performance

Check runtime-specific bottlenecks.

Flag:
- expensive work during cold start
- large serverless bundle
- repeated initialization per request
- no connection reuse where safe
- connection pool misuse
- container memory limit mismatch
- CPU throttling risk
- slow startup probes
- missing readiness behavior
- SSR waterfalls
- blocking server render on non-critical data
- per-request global mutation

Key terms: cold start, connection pooling, startup time, readiness, CPU throttling, memory limit, SSR waterfall.

### Observability and Measurement

Check whether performance can be measured and diagnosed.

Use service signals:
- latency
- traffic/request rate
- errors
- saturation

Use resource signals:
- utilization
- saturation
- errors

Check:
- tracing for critical paths
- metrics for queues and workers
- database query timing
- external dependency timing
- cache hit/miss rate
- memory growth
- CPU hotspots
- p95/p99 latency
- slow logs
- timeout counts
- retry counts
- lock wait time
- deadlock counts
- GC pressure where relevant

Flag performance risks with no way to measure impact.

Key terms: observability, profiling, tracing, metrics, p95, p99, saturation, utilization, error rate.

### Performance Tests and Validation

Check whether performance assumptions are validated at the right level.

Use:
- microbenchmarks for isolated hot algorithms
- profiling for CPU, memory, allocations, and I/O hotspots
- unit tests for bounded behavior and algorithmic edge cases
- concurrency tests for race-prone logic
- integration tests for database queries, transactions, locks, and adapters
- load tests for throughput and latency under expected workload
- stress tests for behavior beyond expected workload
- soak tests for memory leaks and resource leaks over time
- chaos/failure tests for dependency timeouts, retries, and queue behavior
- smoke tests for startup, health, readiness, and basic production path

Flag performance changes without baseline and after-measurement.

Key terms: benchmark, profile, load test, stress test, soak test, concurrency test, baseline, regression threshold.

### Performance Cognitive Debt

Flag cognitive debt when maintainers cannot understand performance behavior without mentally reconstructing hidden caches, implicit batching, async flows, lock ownership, retry behavior, queue semantics, or data growth assumptions.

Reduce cognitive debt by naming hot paths, documenting workload assumptions, making resource ownership explicit, localizing concurrency control, and adding tests or metrics for critical performance behavior.

Do not hide performance behavior behind clever abstractions.

Key terms: performance cognitive debt, hidden cost, implicit concurrency, invisible cache, workload assumption.

## Performance and Scalability Smells

Flag:
- nested loops over growing data
- repeated full scans
- repeated sorting
- N+1 queries
- chatty I/O
- unbounded pagination
- loading entire datasets into memory
- unbounded caches
- unbounded queues
- no timeout on external calls
- retries without backoff or budget
- serial external calls on critical path
- missing batching
- missing indexes
- long transactions
- I/O inside locks or transactions
- read-modify-write without atomicity
- missing idempotency
- shared mutable state across concurrent requests
- async race between stale and fresh data
- leaked listeners, timers, subscriptions, tasks, workers, cursors, files, or connections
- no cleanup on cancellation or failure
- busy waiting
- lock order inconsistency
- excessive frontend re-renders
- large list rendering without virtualization
- layout thrashing
- large payloads or responses
- no metrics for latency, errors, saturation, queue depth, or dependency timing
- performance tests without realistic workload
- benchmarks without baseline or threshold

## Review Rules

Be concrete, falsifiable, and performance-specific.

Do not say:
- Improve performance
- Make it faster
- Optimize this
- Add caching
- Make it scalable
- Fix memory leak
- Handle concurrency
- Add load tests

Instead state:
- Which operation or flow is affected
- Which workload or data size matters
- Which resource is bottlenecked: CPU, memory, disk, network, database, lock, queue, browser main thread, external dependency, or runtime startup
- Which complexity, query, allocation, lock, race, retry, or I/O pattern causes risk
- Which user or system behavior degrades
- Which smallest remediation reduces the bottleneck
- Which measurement or test proves the improvement

Do not optimize cold code before hot code.

Do not introduce caching without invalidation, ownership, and correctness rules.

Do not parallelize work unless ordering, idempotency, resource limits, and failure behavior are safe.

Do not replace simple code with complex code unless measurement or scale assumptions justify it.

## Output Format

For each finding, use:

### Finding: precise performance or scalability issue

Priority: Critical | High | Medium | Low

Category: Workload | Latency | Throughput | Algorithmic Complexity | Memory | Resource Leak | Database | Cache | Concurrency | Race Condition | Deadlock | Queue/Backpressure | External Dependency | Frontend Performance | SSR/Serverless/Container | Observability | Performance Testing | Cognitive Debt

Operation:
Request, job, component, query, flow, algorithm, worker, route, event, or integration affected.

Workload assumption:
Input size, request rate, concurrency, data volume, tenant count, payload size, queue depth, browser/device constraint, or runtime limit.

Issue:
Exact bottleneck, inefficiency, leak, race, contention, deadlock risk, scalability limit, or observability gap.

Evidence:
Specific function, component, query, loop, data structure, lock, transaction, cache, queue, effect, external call, metric, profile, test, or missing measurement.

Impact:
Latency, throughput, memory growth, CPU usage, I/O pressure, database load, lock wait, queue backlog, user responsiveness, availability, cost, or reliability impact.

Recommendation:
Smallest safe remediation.

Validation:
Benchmark, profile, unit test, concurrency test, integration test, load test, stress test, soak test, trace, metric, query plan, smoke test, or production dashboard.

Target shape:
Expected algorithm, query, cache rule, concurrency control, batching, backpressure, resource lifetime, metric, or runtime behavior.

## Audit Sequence

1. Identify the operation, user flow, job, or system path under review.
2. Define workload assumptions and performance expectations.
3. Identify hot paths, critical paths, and scale-sensitive paths.
4. Inspect algorithmic complexity and data growth behavior.
5. Inspect database queries, indexes, pagination, transactions, and locking.
6. Inspect I/O, external calls, serialization, and payload size.
7. Inspect memory allocation, retention, cleanup, and resource lifetime.
8. Inspect concurrency, shared state, idempotency, retries, and update consistency.
9. Inspect locks, transactions, queue behavior, and backpressure.
10. Inspect frontend render cost, network waterfalls, hydration, and cleanup.
11. Inspect runtime-specific concerns: SSR, serverless, containers, workers.
12. Inspect observability: latency, traffic, errors, saturation, utilization, queue depth, dependency timing.
13. Check whether tests or measurements prove the risk and remediation.
14. Recommend the smallest changes that materially improve performance or scalability.

## Complexity Heuristic

For each important operation, ask:

- What is the input size?
- What grows with users, tenants, requests, records, events, files, or queue depth?
- Is the operation O(1), O(log n), O(n), O(n log n), O(n²), or worse?
- Is all data needed, or only a page, window, aggregate, or projection?
- Is work repeated unnecessarily?
- Is the same data fetched, parsed, sorted, serialized, or transformed multiple times?
- Does memory grow with input size, request count, tenant count, or time?
- Is growth bounded by configuration, pagination, eviction, streaming, or backpressure?

If the growth behavior is unclear, the design has performance risk.

## Concurrency Heuristic

For each state-changing operation, ask:

- Can two requests/jobs/events update the same resource concurrently?
- Is the operation idempotent?
- Is read-modify-write protected by transaction, lock, version check, or atomic operation?
- Can retries duplicate side effects?
- Can events arrive out of order?
- Can stale async results overwrite newer state?
- Can locks be acquired in different orders?
- Can work block forever?
- Can producers exceed consumer capacity?
- Is cancellation handled safely?

If the answer is unclear, the design has concurrency risk.

## Memory Leak Heuristic

For each long-lived process, component, worker, or repeated operation, ask:

- What is allocated?
- Who owns it?
- When is it released?
- What happens on error, cancellation, retry, unmount, disconnect, timeout, or shutdown?
- Are listeners, timers, subscriptions, tasks, file handles, cursors, connections, locks, and observers cleaned up?
- Are caches, queues, maps, buffers, and accumulators bounded?
- Does memory stabilize during a soak test?

If ownership and cleanup are unclear, the design has memory/resource leak risk.

## Priority Rules

Critical:
A performance or concurrency issue can cause outage, data corruption, cross-user data mixup, unbounded resource exhaustion, deadlock, queue collapse, runaway cost, or severe production availability impact.

High:
A hot path has clear unbounded growth, N+1 query, missing concurrency control, memory leak, retry storm, lock contention, or missing timeout likely to affect normal production load.

Medium:
A meaningful path has inefficient behavior, weak scalability, partial observability, missing benchmark, missing load validation, or risk under plausible growth.

Low:
The issue is local inefficiency, readability of performance behavior, minor cognitive debt, or hardening without current scale pressure.

## Remediation Strategy

Prefer measurement-guided, behavior-preserving performance work:

1. Define workload and performance expectation.
2. Add or identify baseline measurement.
3. Protect correctness with tests before optimization.
4. Fix algorithmic complexity before micro-optimizing.
5. Reduce unnecessary I/O and round trips.
6. Bound memory, queues, payloads, pagination, and concurrency.
7. Add timeouts, cancellation, backpressure, and retry budgets.
8. Make state changes idempotent and concurrency-safe.
9. Add indexes, batching, projections, or query changes where data access is the bottleneck.
10. Add caching only with explicit key, invalidation, eviction, and correctness rules.
11. Add metrics, traces, profiles, and dashboards for critical paths.
12. Validate improvement with benchmark, profile, load test, stress test, soak test, or production metric.

## Core Principle

Performance and scalability review should prevent real degradation, not produce generic optimization advice.

Every finding must connect a concrete bottleneck, workload, resource, or concurrency risk to impact, smallest remediation, and validation.
