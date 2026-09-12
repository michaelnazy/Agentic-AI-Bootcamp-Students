---
name: sql-explainer-optimiser
description: Explain a raw SQL query in plain English and recommend evidence-based performance or correctness improvements. Use when the user provides uncommented SQL and asks what it does, how to optimise it, or why it may be slow.
---

# Skill: SQL Explainer & Optimiser

## When to use this

Fires on: a raw or uncommented SQL query, especially when the user asks for an explanation, performance review, optimisation, or query improvements.

Does **not** fire on: requests to execute SQL, modify production data, design a complete schema, or answer general database questions without a query to inspect.

## Steps

1. Identify the SQL dialect if the user states it. If no dialect is given, say that the review is dialect-neutral and flag recommendations that depend on PostgreSQL, MySQL, SQL Server, Oracle, or another specific database.
2. Call `read_resource("resources/sql-checklist.md")` before making optimisation recommendations. Treat the checklist as a review aid, not as proof that every item applies.
3. Inspect the query's structure: tables and joins, filters, grouping and aggregation, ordering, subqueries or CTEs, window functions, selected columns, and possible row multiplication.
4. Explain the query in plain English before discussing changes. Describe the result it returns, how rows are matched and filtered, and any important edge cases such as NULL handling, duplicates, or ties.
5. Compare the query against the checklist. Recommend only changes supported by something visible in the query or clearly marked as needing runtime evidence such as an execution plan, table statistics, indexes, or measured workload.
6. For every recommendation, state all three items:
   - **Change:** the concrete SQL, schema, index, or usage change.
   - **Why it helps:** the mechanism, such as fewer rows scanned, less data transferred, better cardinality estimates, fewer round trips, or safer type comparison.
   - **Trade-off or validation:** what could make it unsuitable and what to check, such as an execution plan, representative timings, write overhead, or dialect support.
7. Do not invent schema details, indexes, data volumes, constraints, execution-plan facts, or performance measurements. Mark assumptions explicitly.
8. If no change is justified from the SQL alone, say so and name the smallest piece of evidence needed next, usually an execution plan and table/index definitions.

## Required output

Use this order and these headings:

### Plain-English explanation
A concise explanation of what the query returns and how it gets there. Mention the dialect assumption when relevant.

### Issues found
A short list of concrete risks or inefficiencies visible in the query. Write `None identified from the SQL alone` when appropriate.

### Recommended improvements
For each recommendation, use this format:

1. **Change:** ...
   **Why it helps:** ...
   **Trade-off or validation:** ...

Do not provide a recommendation that lacks a why. Do not present a generic checklist dump as an optimisation review.

### What to verify next
List the runtime evidence needed to confirm the highest-impact recommendations, such as `EXPLAIN` or `EXPLAIN ANALYZE`, relevant index definitions, row counts, parameter types, and representative timings.

## Rules

- Preserve the user's query semantics unless you explicitly label a proposal as a semantic change.
- Never claim that an index, hint, rewrite, or join order will improve performance without explaining the mechanism and the conditions under which it may help.
- Treat index hints as dialect-specific and as a last resort after checking the execution plan; a hint can force a worse plan as data changes.
- Distinguish correctness problems from performance opportunities.
- Prefer a small, concrete rewrite or diagnostic step over broad advice.
- Keep the final answer understandable to a reader who knows SQL basics but is not a database specialist.
