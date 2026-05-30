# Treemap

**Use when**: showing part-to-whole across many categories (where a pie chart would have too many slices); displaying hierarchical data in a compact space; exploratory analysis where high-level size patterns matter more than precise values.  
**Avoid when**: data contains zero or negative values (area encoding can't represent them); precise comparisons between similarly-sized rectangles are needed; the audience is unfamiliar with the format.

## Key rules

- Sort rectangles largest → smallest from top-left to bottom-right (squarified algorithm default)
- Use color for **either** hierarchy levels **or** a quantitative dimension — not both simultaneously
- Enable hover/tooltip to display values for unlabeled small segments
- Prioritize direct labels on larger rectangles; rely on interactivity for smaller ones
- If you need precise comparisons, use a horizontal bar chart instead

## Anti-patterns

- Treemap with zero or negative values — area must be positive; consider a bar chart
- Using treemaps when there's no hierarchy — a bar chart communicates flat categorical data more clearly
- Aesthetic-driven treemap selection — the squarified layout looks impressive but doesn't justify itself if a simpler chart answers the question

→ [Storytelling with Data: What is a treemap?](https://www.storytellingwithdata.com/blog/what-is-a-treemap)
