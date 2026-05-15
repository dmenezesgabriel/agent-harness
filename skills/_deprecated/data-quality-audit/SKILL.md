---
name: data-quality-audit
description: Audit data, schemas, pipelines, transformations, datasets, events, reports, dashboards, ML features, and application persistence for correctness, completeness, consistency, validity, freshness, uniqueness, integrity, lineage, reconciliation, and business fitness.
---

## Purpose

Audit data quality risks that can reduce correctness, trust, analytical validity, operational reliability, reporting accuracy, ML performance, user experience, or business decision quality.

Use data quality dimensions, domain rules, schema contracts, reconciliation, lineage, anomaly detection, freshness checks, referential integrity, observability, and risk-based validation.

This playbook is language-agnostic and tool-agnostic.

## When to Use

Use when reviewing:
- database tables
- application data models
- ETL/ELT pipelines
- ingestion jobs
- event streams
- message schemas
- APIs that produce or consume data
- analytics models
- metrics layers
- dashboards
- reports
- ML training datasets
- ML features
- data migrations
- data backfills
- deduplication logic
- transformations
- data contracts
- source-to-target mappings
- reconciliation logic
- data observability checks
- production incidents caused by bad data

Do not audit unrelated datasets or pipelines unless the requested change depends on them.

## Core Principle

Data quality is fitness for use.

A data quality finding must identify:
- data product, table, event, field, metric, or flow affected
- consumer or business process affected
- quality dimension violated
- rule, contract, or expectation that should hold
- evidence or missing validation
- impact
- smallest safe remediation
- validation or monitoring method

Do not treat schema validity alone as data quality.

Valid data can still be wrong, stale, incomplete, duplicated, inconsistent, misleading, or unfit for its consumer.

## Data Quality Dimensions

Use these dimensions as audit categories.

### Accuracy

Check whether data represents the real-world fact, source-of-truth value, business event, or intended domain concept correctly.

Flag:
- incorrect values
- wrong source mapping
- wrong currency, timezone, unit, locale, or precision
- stale snapshot treated as current
- derived values that do not match source facts
- incorrect business rule implementation
- manual overrides without traceability
- ML labels or features that do not represent the target concept

Key terms: accuracy, correctness, source of truth, real-world fact, semantic correctness.

### Completeness

Check whether required data is present at the required grain.

Flag:
- missing rows
- missing columns
- missing required fields
- nulls in required attributes
- partial ingestion
- missing partitions
- missing event types
- incomplete joins
- silently dropped records
- incomplete backfills
- optional fields that are required by downstream consumers

Key terms: completeness, missingness, null rate, coverage, required field, required row.

### Consistency

Check whether the same concept has compatible values across systems, tables, events, reports, and time.

Flag:
- conflicting values across sources
- inconsistent business definitions
- inconsistent metric logic
- mismatched enum values
- incompatible status transitions
- different timezone/unit/currency assumptions
- inconsistent aggregation grain
- multiple definitions for the same field
- dashboard metric mismatch with source system

Key terms: consistency, semantic consistency, cross-system consistency, metric consistency, definition drift.

### Validity

Check whether data conforms to allowed formats, domains, schemas, ranges, patterns, and types.

Flag:
- invalid enum values
- invalid dates
- impossible numeric ranges
- malformed identifiers
- invalid email/URL/phone formats where relevant
- wrong data types
- schema violations
- invalid JSON/event payloads
- invalid status transitions
- invalid categorical values

Key terms: validity, schema validation, domain constraint, allowed values, type constraint.

### Uniqueness

Check whether records that should be unique are unique at the correct grain.

Flag:
- duplicate primary keys
- duplicate business keys
- duplicate events
- duplicate users/customers/orders
- duplicate rows after joins
- duplicated facts across partitions
- missing idempotency
- ambiguous natural keys
- deduplication that loses valid records
- deduplication that keeps the wrong record

Key terms: uniqueness, deduplication, primary key, business key, natural key, idempotency.

### Timeliness and Freshness

Check whether data arrives, updates, and becomes available within the expected time window.

Flag:
- stale tables
- late-arriving data without handling
- delayed partitions
- outdated dashboards
- missing freshness checks
- wrong event-time vs processing-time semantics
- pipelines that succeed with old input
- no SLA/SLO for critical data
- ML features older than acceptable for serving

Key terms: timeliness, freshness, recency, latency, event time, processing time, SLA, SLO.

### Integrity

Check whether relationships, references, constraints, and invariants hold.

Flag:
- orphan records
- broken foreign keys
- invalid parent-child relationships
- inconsistent totals
- broken state-machine transitions
- facts without dimensions
- dimensions without valid effective dates
- overlapping slowly changing dimension ranges
- many-to-many joins where one-to-one is expected
- referential rules enforced only downstream

Key terms: integrity, referential integrity, invariant, relationship constraint, state transition.

### Conformity and Standardization

Check whether data follows expected standards and canonical representations.

Flag:
- inconsistent casing
- inconsistent whitespace
- inconsistent country/currency/language codes
- inconsistent date formats
- unnormalized units
- unstandardized names
- ambiguous free-text categories
- inconsistent identifiers
- locale-specific formatting leaking into storage

Key terms: conformity, standardization, canonical form, normalization, controlled vocabulary.

### Precision and Granularity

Check whether precision, rounding, aggregation level, and record grain match the use case.

Flag:
- money rounded too early
- floating-point error in financial values
- timestamps truncated incorrectly
- metrics aggregated at wrong grain
- user-level data mixed with account-level data
- event-level and session-level concepts mixed
- averages of averages
- ratios aggregated incorrectly
- loss of detail needed for audit or reconciliation

Key terms: precision, granularity, grain, aggregation level, rounding, numerical stability.

### Lineage and Traceability

Check whether data can be traced from source to transformation to consumer.

Flag:
- unknown source
- undocumented transformation
- no source-to-target mapping
- no versioned business definition
- no audit trail for manual corrections
- no run metadata
- no dataset ownership
- no reproducible backfill
- no explanation for metric changes
- no lineage for regulated or critical data

Key terms: lineage, provenance, traceability, source-to-target mapping, audit trail, ownership.

### Relevance and Fitness for Use

Check whether data is appropriate for the consumer’s decision, product behavior, report, or model.

Flag:
- technically valid data that does not answer the business question
- obsolete fields used in new logic
- proxy variables used without validation
- metrics that do not match business intent
- ML labels that do not represent the prediction target
- data used outside its collection context
- dashboard fields without owner or consumer
- stale business definitions

Key terms: fitness for use, relevance, business meaning, data product, consumer contract.

## Review Principles

### Data Contract

Check whether producers and consumers share an explicit contract.

Review:
- schema
- field meanings
- required fields
- nullable fields
- allowed values
- primary/business keys
- event semantics
- timestamp semantics
- ownership
- freshness expectation
- compatibility rules
- deprecation rules

Flag producer changes that can silently break consumers.

Key terms: data contract, schema contract, compatibility, producer, consumer, semantic versioning.

### Source of Truth

Check whether the authoritative source for each concept is explicit.

Flag:
- multiple competing sources of truth
- unclear precedence rules
- manual overrides without ownership
- reports using non-authoritative copies
- transformed data used as source truth without declaration
- inconsistent source selection across pipelines

Key terms: source of truth, system of record, precedence, canonical source.

### Grain and Identity

Check whether each dataset has one clear grain and stable identity.

Flag:
- mixed grains in one table
- ambiguous row meaning
- missing primary key
- unstable natural key
- incorrect uniqueness expectation
- one-to-many join accidentally duplicating facts
- event identity confused with entity identity
- snapshot rows confused with event rows

Key terms: grain, entity, event, snapshot, primary key, business key, identity.

### Transformation Correctness

Check whether transformations preserve meaning and enforce business rules.

Flag:
- filters that silently drop records
- joins that duplicate or lose records
- wrong join type
- many-to-many join explosion
- aggregation at wrong level
- window function with wrong partition/order
- incorrect timezone conversion
- incorrect currency/unit conversion
- ordering-dependent logic without deterministic ordering
- null handling that changes meaning
- default values that hide missing data

Key terms: transformation, join cardinality, aggregation, window function, null semantics, deterministic order.

### Reconciliation

Check whether important totals, counts, balances, and records reconcile across stages and sources.

Flag:
- no source-to-target row count check
- no sum/balance reconciliation
- no partition completeness check
- no duplicate count check
- no rejected-record accounting
- no late-arriving record accounting
- no financial/control total reconciliation
- no migration before/after comparison

Key terms: reconciliation, control total, source-to-target, row count, checksum, balance check.

### Drift and Anomaly Detection

Check whether data changes are monitored over time.

Flag:
- sudden null-rate change
- sudden volume change
- category distribution shift
- new enum value
- missing partition
- metric spike/drop without explanation
- feature drift
- label drift
- schema drift
- seasonal pattern treated as anomaly without context

Key terms: drift, anomaly detection, distribution shift, schema drift, data observability.

### Error Handling and Quarantine

Check whether bad data is rejected, quarantined, corrected, or surfaced safely.

Flag:
- invalid records silently dropped
- invalid records silently coerced
- pipeline succeeds with critical validation failures
- no rejected-record table
- no error reason
- no retry/reprocess path
- no owner notification
- no threshold for failure
- bad data mixed with trusted data

Key terms: quarantine, rejected records, data quality threshold, failure policy, remediation path.

### Observability and Ownership

Check whether data quality can be monitored and owned.

Review:
- dataset owner
- consumer owner
- freshness checks
- volume checks
- quality score
- alert thresholds
- run metadata
- lineage
- failed validations
- incident history
- downstream impact
- SLA/SLO

Flag critical datasets without ownership, monitoring, or alerting.

Key terms: data observability, ownership, SLA, SLO, alert, run metadata.

### Privacy, Governance, and Sensitive Data

Check whether data quality controls preserve privacy and governance expectations.

Flag:
- sensitive data in non-sensitive datasets
- missing classification
- PII duplicated unnecessarily
- retention rules not enforced
- deleted users still present downstream
- masking/tokenization inconsistent
- unauthorized fields exposed to analytics, logs, or dashboards
- data quality tests leaking sensitive sample values

Key terms: data governance, classification, PII, retention, masking, minimization.

### ML Data Quality

Check whether model datasets and features are correct, representative, and reproducible.

Flag:
- label leakage
- train/serve skew
- target leakage
- feature freshness mismatch
- missing feature backfill validation
- biased missingness
- unrepresentative sample
- duplicate entities across train/test split
- non-reproducible dataset build
- feature definition drift
- label delay not handled
- class imbalance ignored where relevant

Key terms: train/serve skew, label leakage, feature drift, reproducibility, sample bias.

### Dashboard and Metric Quality

Check whether reports and dashboards express reliable business metrics.

Flag:
- metric definition not documented
- filters inconsistent with business intent
- dashboard uses stale model
- aggregation grain mismatch
- total does not reconcile with source
- percentage denominator unclear
- timezone cutoff mismatch
- incomplete dimensions causing hidden null bucket
- chart hides missing data
- dashboard lacks freshness indication

Key terms: metric contract, semantic layer, dashboard trust, business definition, denominator, freshness indicator.

### Data Quality Tests

Check whether important rules are tested and monitored.

Use:
- schema tests
- not-null tests
- uniqueness tests
- accepted-values tests
- relationship tests
- range tests
- freshness tests
- volume tests
- row-count reconciliation
- aggregate reconciliation
- distribution checks
- anomaly detection
- contract tests
- migration diff checks
- backfill validation
- dashboard metric validation
- ML feature/label validation

Flag tests that only check technical schema while business-critical correctness is untested.

Key terms: data test, expectation, assertion, quality gate, data contract test.

### Data Cognitive Debt

Flag data cognitive debt when maintainers or analysts must infer hidden business definitions, undocumented transformations, unclear ownership, ambiguous grain, implicit source precedence, or scattered metric logic.

Reduce data cognitive debt by naming concepts, documenting grain, defining contracts, centralizing metric definitions, recording lineage, and making quality checks executable.

Do not hide business definitions in ad hoc SQL, dashboard filters, or pipeline glue code.

Key terms: data cognitive debt, semantic ambiguity, hidden metric, unclear grain, implicit lineage.

## Data Quality Smells

Flag:
- no declared owner
- no declared grain
- no source of truth
- no primary or business key
- no freshness expectation
- no required-field contract
- no accepted-values contract
- no schema compatibility policy
- no lineage
- no reconciliation
- no rejected-record handling
- no null-rate monitoring
- no duplicate monitoring
- no late-arriving data strategy
- no backfill validation
- no migration validation
- no dashboard freshness indicator
- no metric definition owner
- joins without cardinality checks
- filters that silently drop records
- default values that hide missingness
- invalid data silently coerced
- pipeline succeeds with stale input
- duplicated metric logic across reports
- source-system fields renamed without semantic mapping
- timestamps without timezone semantics
- money without currency semantics
- IDs reused across tenants without tenant key
- ML features built differently in training and serving

## Review Rules

Be concrete, falsifiable, and data-specific.

Do not say:
- Improve data quality
- Add checks
- Validate the data
- Fix bad data
- Add monitoring
- Improve metrics
- Clean the dataset

Instead state:
- Which dataset, field, event, metric, or transformation is affected
- Which consumer or business process depends on it
- Which quality dimension is violated
- Which rule, contract, or invariant should hold
- Which data defect can escape
- Which validation is missing or weak
- Which smallest remediation improves trust
- Which monitoring or test proves the fix

Do not require every possible check.

Prioritize critical data elements, critical flows, high-impact metrics, external contracts, regulated data, ML features, and data used for decisions or automation.

Do not treat passing schema checks as proof of correctness.

Do not silently coerce invalid data unless the correction rule is explicit, tested, and auditable.

## Output Format

For each finding, use:

### Finding: precise data quality issue

Priority: Critical | High | Medium | Low

Category: Accuracy | Completeness | Consistency | Validity | Uniqueness | Freshness | Integrity | Conformity | Precision | Lineage | Fitness for Use | Contract | Source of Truth | Grain | Transformation | Reconciliation | Drift | Error Handling | Observability | Governance | ML Data | Metric Quality | Data Testing | Cognitive Debt

Data asset:
Table, field, event, metric, dashboard, report, model feature, dataset, API payload, file, pipeline, or transformation affected.

Consumer:
User, report, ML model, service, downstream table, business process, compliance process, or operational workflow affected.

Issue:
Exact data quality problem.

Evidence:
Specific field, query, schema, sample pattern, test gap, transformation, join, source mismatch, freshness gap, lineage gap, or monitoring gap.

Quality rule:
The invariant, contract, expectation, threshold, business rule, or reconciliation rule that should hold.

Impact:
Incorrect decision, broken product behavior, bad report, model degradation, data loss, duplicate processing, compliance risk, operational incident, or loss of trust.

Recommendation:
Smallest safe remediation.

Validation:
Data test, contract test, reconciliation, query check, anomaly monitor, freshness check, migration diff, backfill validation, dashboard validation, or manual source verification.

Target shape:
Expected schema, rule, contract, grain, lineage, reconciliation, ownership, monitoring, or remediation behavior.

## Audit Sequence

1. Identify the data asset and its consumers.
2. Identify critical data elements, metrics, events, and business rules.
3. Confirm source of truth, ownership, grain, identity, and lineage.
4. Inspect schema, required fields, accepted values, ranges, and formats.
5. Inspect freshness, completeness, volume, partitions, and late-arriving data.
6. Inspect uniqueness, duplicate handling, keys, and idempotency.
7. Inspect joins, filters, aggregations, null handling, and transformations.
8. Inspect referential integrity, state transitions, and cross-table consistency.
9. Inspect reconciliation against source, target, and control totals.
10. Inspect drift, anomaly detection, and quality monitoring.
11. Inspect rejected-record handling, remediation workflow, and alerting.
12. Inspect privacy, retention, masking, and governance where relevant.
13. Inspect ML feature/label quality where relevant.
14. Inspect dashboard and metric definitions where relevant.
15. Check whether tests prove the quality rules that matter.
16. Recommend the smallest changes that materially improve data trust.

## Data Quality Test Heuristic

For each critical data element or metric, ask:

- What proves required values are present?
- What proves values are valid?
- What proves values are accurate enough for the consumer?
- What proves records are unique at the correct grain?
- What proves relationships are intact?
- What proves data is fresh enough?
- What proves transformations preserve counts, sums, and meaning?
- What proves joins do not duplicate or drop records unexpectedly?
- What proves source and target reconcile?
- What proves late, invalid, or duplicate records are handled safely?
- What proves metric definitions match business intent?
- What proves previous data incidents cannot return?

If none of these answers are clear, the data quality coverage is weak.

## Priority Rules

Critical:
Bad data can cause financial misstatement, compliance violation, unsafe automation, cross-tenant/user data corruption, irreversible data loss, production outage, severe ML decision error, or critical business decision failure.

High:
Critical data asset lacks validation for correctness, completeness, uniqueness, freshness, integrity, reconciliation, or contract compatibility, and downstream consumers can be materially affected.

Medium:
Important data has partial validation, unclear ownership, weak lineage, missing drift monitoring, ambiguous grain, or untested transformation assumptions.

Low:
The issue mainly affects maintainability, documentation, discoverability, minor reporting trust, or cognitive debt without immediate high-impact consumer risk.

## Remediation Strategy

Prefer risk-based, executable data quality improvements:

1. Define the consumer and quality rule.
2. Identify source of truth and grain.
3. Add the smallest data test that proves the rule.
4. Add reconciliation for critical counts, sums, balances, or records.
5. Add freshness and volume monitoring for critical pipelines.
6. Add uniqueness and relationship checks at the correct grain.
7. Make invalid data fail, quarantine, or alert according to impact.
8. Make transformations deterministic and auditable.
9. Centralize metric definitions or data contracts where duplication creates risk.
10. Add lineage and ownership for critical assets.
11. Validate migrations and backfills with before/after comparisons.
12. Monitor drift and anomalies for high-value datasets.
13. Keep checks close to the data boundary or transformation they protect.

## Core Principle

Data quality audit should protect trust in data used by software, people, reports, models, and business decisions.

Every finding must connect a concrete data defect or missing quality control to a consumer, business rule, impact, smallest remediation, and validation method.
