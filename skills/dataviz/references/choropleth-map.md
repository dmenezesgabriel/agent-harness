# Choropleth Map

**Use when**: the geographic pattern itself is the insight and data is normalized per region (rate, percentage, density) — not raw counts.  
**Avoid when**: data is count-based without normalization — large-area regions dominate visually regardless of actual value; precise regional comparison is needed (a bar chart ranked by value is clearer); many regions have no data.

## Key rules

- Always normalize: use rate, percentage, or per-capita values — raw counts make large-area regions look dominant
- Use a sequential palette (light → dark) for a single metric; use a diverging palette (two hues from a neutral midpoint) when values span a meaningful zero
- Limit to 5–7 color steps — more steps require a legend readers can't mentally map
- Include a clear legend with labeled breakpoints
- Add a tooltip or annotation layer for precise values — color alone is imprecise

## Anti-patterns

- Raw counts on a choropleth — population size, not the metric of interest, drives the visual
- Rainbow palette (red → yellow → green) — the perceptual distance between colors is uneven and implies non-existent thresholds
- Missing regions shown as white — indistinguishable from "zero value"; use a distinct pattern or gray for no-data regions

→ [Storytelling with Data: What is a choropleth map?](https://www.storytellingwithdata.com/blog/what-is-a-choropleth-map)
