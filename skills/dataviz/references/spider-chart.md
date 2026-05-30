# Spider Chart / Radar Chart

**Avoid in most cases.** Angle and area comparisons on a radial grid are cognitively difficult — readers cannot reliably judge whether one polygon is larger than another, and axis ordering arbitrarily inflates or deflates the enclosed area.

**Use only when**: showing a multivariate profile where the "shape" is the message and all axes are on comparable scales (e.g., a sports player's skill profile where relative shape across roles is what matters).  
**Avoid when**: precise comparison between entities is needed; axes have different units or scales; the audience is unfamiliar with radial charts.

## Preferred alternatives

- **Grouped bar chart** — for comparing multiple metrics across a small number of categories
- **Parallel coordinates plot** — for comparing many attributes across many entities
- **Small multiples of bar charts** — one bar chart per attribute, same scale

## Key rules (if you must use one)

- Keep to ≤ 5–6 axes — more axes compress the inner region and make small values invisible
- Use consistent axis scales — mixing units or ranges makes area comparisons meaningless
- Limit to 2–3 overlapping series — more than that and the polygons obscure each other

→ [Storytelling with Data: What is a spider chart?](https://www.storytellingwithdata.com/blog/2021/8/31/what-is-a-spider-chart)
