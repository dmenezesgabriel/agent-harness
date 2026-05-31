## Evaluation run - all phase context is provided below. Build directly.

**Story (Phase 1)**
- Audience: Executives deciding next-quarter regional investment.
- Decision: Which regions need attention, and whether growth is broad-based or concentrated.
- Key takeaway: West is pulling away while Southeast is declining.
- Questions: (1) How does revenue trend by region? (2) Which region grew fastest? (3) Which region needs intervention?

**Data (Phase 2 - already inspected)**
Inline data - no file path needed:

| month   | region    | revenue | operating_margin |
|---------|-----------|---------|------------------|
| 2024-01 | Northeast | 125000  | 0.18             |
| 2024-01 | Southeast | 98000   | 0.12             |
| 2024-01 | Midwest   | 110000  | 0.15             |
| 2024-01 | West      | 145000  | 0.22             |
| 2024-02 | Northeast | 131000  | 0.19             |
| 2024-02 | Southeast | 92000   | 0.10             |
| 2024-02 | Midwest   | 118000  | 0.16             |
| 2024-02 | West      | 152000  | 0.24             |
| 2024-03 | Northeast | 128000  | 0.17             |
| 2024-03 | Southeast | 87000   | 0.09             |
| 2024-03 | Midwest   | 124000  | 0.18             |
| 2024-03 | West      | 160000  | 0.25             |
| 2024-04 | Northeast | 142000  | 0.20             |
| 2024-04 | Southeast | 89000   | 0.08             |
| 2024-04 | Midwest   | 128000  | 0.19             |
| 2024-04 | West      | 167000  | 0.26             |

**Chart plan (Phase 3 - approved)**
| Question | Data path in tree | Chart type | Why |
|---|---|---|---|
| Revenue trend by region | TIME SERIES -> several series (<7) | Multi-line chart | 4 ordered regional series |
| Latest regional comparison | Numeric + Categoric -> one obs/group -> 1 numeric | Horizontal bar | compares April revenue by region |
| Margin context | Numeric + Categoric -> one obs/group -> 1 numeric | Dot plot or bar | compares April operating margin |

**Theme**: Financial Times inspired, but keep colors colorblind-safe.

**Output**: Build a small dashboard with KPI cards, at least two charts, direct labels or clear legends, source/time-period note, explicit hardcoded colors, no 3D, no dual y-axes, and no red-green pairing.
