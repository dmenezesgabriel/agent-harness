## Evaluation run — all phase context is provided below. Build directly.

**Story (Phase 1)**
- Audience: Business analysts reviewing quarterly performance
- Decision: Which regions need investment? Is overall revenue growing?
- Key takeaway: Revenue trends diverge across regions over 2024
- Questions: (1) How does monthly revenue trend per region? (2) Which region is growing fastest?

**Data (Phase 2 — already inspected)**
Inline data — no file path needed:

| month   | region    | revenue |
|---------|-----------|---------|
| 2024-01 | Northeast | 125000  |
| 2024-01 | Southeast | 98000   |
| 2024-01 | Midwest   | 110000  |
| 2024-01 | West      | 145000  |
| 2024-02 | Northeast | 131000  |
| 2024-02 | Southeast | 92000   |
| 2024-02 | Midwest   | 118000  |
| 2024-02 | West      | 152000  |
| 2024-03 | Northeast | 128000  |
| 2024-03 | Southeast | 87000   |
| 2024-03 | Midwest   | 124000  |
| 2024-03 | West      | 160000  |
| 2024-04 | Northeast | 142000  |
| 2024-04 | Southeast | 89000   |
| 2024-04 | Midwest   | 128000  |
| 2024-04 | West      | 167000  |

**Chart plan (Phase 3 — approved)**
| Question | Data path in tree | Chart type | Why |
|---|---|---|---|
| Revenue trend per region | TIME SERIES → several series (<7) | Multi-line chart | 4 time-ordered series, 1 measure |

**Theme**: Clean analytical

**Output**: Apply all design rules from the skill: explicit colors (max 7, colorblind-safe), no 3D, no dual y-axes, zero baseline on y-axis, direct labels. Hardcode the inline data above. Use whatever output format the skill prescribes (Vite app, HTML, or notebook).
