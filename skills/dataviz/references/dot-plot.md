# Dot Plot

**Use when**: comparing a moderate number of items on a single numeric scale where the exact position matters more than a bar's cumulative length; highlighting that values don't start at zero.  
**Avoid when**: the audience expects bars and the zero-baseline matters for the message; too many items (> ~30) — dots become a wall.

## Key rules

- Sort dots by value to make ranking legible
- Use a **dumbbell (connected dot) plot** for before/after pairs — the connecting line makes the direction and magnitude of change explicit
- No zero baseline required — position on the scale is the encoding, not length from zero
- Direct-label the dots' values when precision matters; otherwise let the axis do the work
- Horizontal orientation usually reads better when category names vary in length

## Anti-patterns

- Dot plot with an alphabetical sort — obscures ranking and comparison
- Using dots for time series with many points — use a line graph instead

→ [Storytelling with Data: What is a dot plot?](https://www.storytellingwithdata.com/blog/2020/12/9/what-is-a-dot-plot)
