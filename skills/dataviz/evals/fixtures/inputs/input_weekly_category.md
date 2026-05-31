## Evaluation run - all phase context is provided below. Build directly.

**Story (Phase 1)**
- Audience: Store manager reviewing weekly category sales.
- Decision: Which category needs more shelf space next week?
- Key takeaway: Groceries outsold other categories by a wide margin.
- Questions: Which category sold the most units this week?

**Data (Phase 2 - already inspected)**
Inline data - no file path needed:

| category    | units_sold |
|-------------|------------|
| Groceries   | 420        |
| Home Goods  | 210        |
| Electronics | 155        |
| Apparel     | 185        |

**Chart plan (Phase 3 - approved)**
| Question | Data path in tree | Chart type | Why |
|---|---|---|---|
| Which category sold most? | Numeric + Categoric -> one obs/group -> 1 numeric | Horizontal bar | ranks discrete categories |

**Theme**: Clean analytical.

**Output**: Build one chart with a zero baseline, explicit color, concise title, data source note, and no decorative chartjunk.
