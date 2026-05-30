# Bubble Chart

**Use when**: three numeric dimensions all vary enough to be visually distinct and the 3-way comparison is the point.  
**Avoid when**: bubble sizes cluster similarly (the 3rd dimension adds noise, not insight — use scatter instead); the audience needs precise magnitude comparisons (humans struggle comparing areas); cognitive load is already high from other charts on the dashboard.

## Key rules

- Verify that the 3rd dimension (bubble size) has enough variation to be visually meaningful before committing to this chart type
- Narrate piece-by-piece for unfamiliar audiences — walk through x, then y, then size
- Label key data points directly; rely on interactivity (tooltips) for the rest
- Size bubbles by area, not radius — most tools default to area, but verify
- Max 4 encoding dimensions (x, y, size, color) before splitting into simpler charts

## Anti-patterns

- All bubbles roughly the same size — the size dimension communicates nothing; drop to a scatterplot
- Using bubble size to encode a categorical variable — area doesn't convey category membership
- Overloading with a 5th dimension (animation + color + size + x + y) — working memory limit is 4 simultaneous encodings

→ [Storytelling with Data: What is a bubble chart?](https://www.storytellingwithdata.com/blog/2021/5/11/what-is-a-bubble-chart)
