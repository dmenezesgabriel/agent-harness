# Box Plot (Box-and-Whisker)

**Use when**: comparing distributions across multiple groups side by side; showing median, spread, and outliers at a glance.  
**Avoid when**: the audience lacks statistical literacy and no live narration is available; precise distribution shape matters (bimodal, skewed) — use histogram or violin plot instead.

## Key rules

- For non-technical audiences: narrate the chart structure before revealing it — explain median, IQR, whiskers, and outliers explicitly
- Use horizontal orientation when category names are long
- Add raw data points (jittered) on top of the box when n is small (< ~30 per group) — the box alone misleads at low sample sizes
- Annotate the median line with its value for readability
- Order groups by median value (or another meaningful sort) rather than alphabetically

## Anti-patterns

- Presenting a fully-formed boxplot to a general audience without explanation — they disengage or misread it
- Using boxplots for a single group — a histogram or density plot shows the shape better
- Hiding multimodal distributions — a bimodal dataset looks like a wide box; combine with a violin or jittered points

→ [Storytelling with Data: What is a boxplot?](https://www.storytellingwithdata.com/blog/what-is-a-boxplot)
