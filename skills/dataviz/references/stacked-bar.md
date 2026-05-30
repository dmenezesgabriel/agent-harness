# Stacked Bar Chart

**Use when**: the primary message is the *total* bar length; the subcomponent breakdown is secondary context.  
**Avoid when**: comparing subcomponents across bars is the goal — only the baseline segment has an aligned axis, making all other segments unreliable to compare precisely.

## Key rules

- Place the most important category at the baseline (bottom for vertical, left for horizontal)
- Add white borders between segments when colors lack sufficient contrast
- Keep bar-to-gap ratio consistent with standard bars (gap ≈ 30–35% of bar width)
- If subcomponent comparison is the actual goal, use grouped bars or separate charts instead
- Label total values at the top/end of each bar; label segments only if space permits and they're readable

## Anti-patterns

- Using stacked bars to compare a middle segment across groups — readers must mentally subtract floating baselines
- Too many stacked segments (5+) — the smallest slices become invisible and unreadable
- Stacking when the total is meaningless (e.g., averaging percentages that don't sum to a coherent whole)

→ [Storytelling with Data: Stacked bars](https://www.storytellingwithdata.com/blog/stacked-bars)
