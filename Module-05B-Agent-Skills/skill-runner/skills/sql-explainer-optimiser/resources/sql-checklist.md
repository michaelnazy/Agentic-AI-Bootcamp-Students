# SQL Review Checklist

Use this checklist to guide a query review. An item is a prompt for investigation,
not proof that the query is wrong. Confirm recommendations with the database
dialect, schema, execution plan, and representative data.

## 1. `SELECT *`

- [ ] Does the query select columns that the caller actually needs?
- [ ] Replace `SELECT *` with an explicit column list when the result is an API,
      report, join, or frequently executed query.
- **Why it matters:** Selecting unnecessary columns increases disk reads, memory
  use, network transfer, and serialization work. It can also prevent a covering
  index from satisfying the query and makes the result fragile when the schema
  changes.
- **Check:** Confirm that removing columns does not change a required contract.
  For exploratory queries, `SELECT *` may be acceptable.

## 2. Missing or inappropriate index guidance

- [ ] Are columns used repeatedly in selective `WHERE` predicates, join
      conditions, or useful `ORDER BY` clauses supported by suitable indexes?
- [ ] Could a composite index match the common predicate and ordering together?
- [ ] Is the query relying on an index hint, or does the dialect support one that
      is being considered because the optimiser chose poorly?
- **Why it matters:** A suitable index can avoid scanning many irrelevant rows
  and reduce sorting or lookup work. A missing index can make a selective query
  degrade into a table scan.
- **Trade-off:** Indexes consume storage and slow inserts, updates, and deletes.
  Column order matters for composite indexes, and low-selectivity columns may
  not benefit. Do not prescribe an index without checking the execution plan,
  existing indexes, and workload.
- **Check:** Use the dialect's plan tool, such as `EXPLAIN`, and inspect actual
  row counts where available. Treat index hints as dialect-specific last resorts:
  a forced plan can become worse as statistics and data distribution change.

## 3. N+1 query problems

- [ ] Does application code run one query to fetch parent rows and then one
      additional query per parent row?
- [ ] Is a correlated subquery or repeated lookup hiding the same pattern?
- [ ] Can the data be fetched with a set-based join, batch query, aggregation, or
      carefully designed eager load?
- **Why it matters:** N rows can cause N+1 database round trips. Network latency,
  connection usage, parsing, and repeated work grow with the number of parents,
  even when each individual query is fast.
- **Trade-off:** A large join can create duplicate rows or transfer too much
  data. Preserve the intended cardinality and compare a batch or set-based
  alternative with measured timings.
- **Check:** Count database calls for one request and test with a realistic number
  of parent rows, not only a small development dataset.

## 4. Implicit casts and type mismatches

- [ ] Do compared or joined columns and parameters have the same data type?
- [ ] Are numeric, date, UUID, or text values being compared across different
      types?
- [ ] Is a database converting a column for every row rather than converting a
      parameter once?
- **Why it matters:** An implicit conversion can prevent an index from being
  used, increase CPU work, cause poor cardinality estimates, or produce surprising
  comparison behavior. It may also fail when values cannot be converted safely.
- **Recommendation:** Bind parameters with the column's native type and use an
  explicit cast only when its direction and semantics are intentional.
- **Check:** Confirm the database's conversion rules and inspect the execution
  plan. The exact risk is dialect-specific.

## 5. Functions wrapped around indexed columns

- [ ] Does a `WHERE` or `JOIN` expression apply a function to an indexed column,
      such as `LOWER(email)`, `DATE(created_at)`, `CAST(order_id AS text)`, or
      arithmetic on the column?
- [ ] Can the predicate be rewritten as a sargable range or compared to a
      precomputed value?
- **Why it matters:** Applying a function may stop the optimiser from using a
      normal index on the original column, forcing a scan or extra computation.
- **Possible improvements:** Use a range predicate for dates, normalise values
  before storage, use a functional or expression index where supported, or add a
  persisted/generated column with an index.
- **Trade-off:** Rewrites must preserve boundary and time-zone semantics.
  Functional indexes and generated columns add write and storage cost and are
  not portable across all databases.
- **Check:** Compare the execution plan before and after the change.

## Additional quick checks

- [ ] Join conditions are complete and do not accidentally create a Cartesian
      product or multiply rows.
- [ ] Filters are applied at the correct stage, especially with `LEFT JOIN`,
      `HAVING`, `NULL`, and three-valued logic.
- [ ] `ORDER BY`, `GROUP BY`, `DISTINCT`, and window functions are necessary and
      supported by the intended access path.
- [ ] Pagination is stable and appropriate for the workload; deep `OFFSET`
      pagination may repeatedly scan and discard rows.
- [ ] Subqueries and CTEs are checked for repeated work, materialisation behavior,
      and semantic differences when rewritten as joins.
- [ ] Returned row volume is reasonable for the caller and bounded where an
      accidental large result would be harmful.
- [ ] Parameters are bound rather than concatenated into SQL, and any security
      concern is called out separately from performance.

## Evidence to request when the SQL is not enough

- Database engine and version.
- Table definitions, constraints, and existing indexes.
- Estimated and actual row counts.
- `EXPLAIN` or `EXPLAIN ANALYZE` output, with care around production execution.
- Representative parameter values and data distribution.
- Query frequency, latency target, and read/write workload.
