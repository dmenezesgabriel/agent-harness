# Pie Chart / Donut Chart

**Use when**: conveying that one segment is notably dominant or negligible; rough part-to-whole understanding is all the audience needs.  
**Avoid when**: precise comparisons between slices are needed; more than 5 categories; slices don't sum to a meaningful 100%.

## Key rules

- Sort by descending size (largest slice starting at 12 o'clock, going clockwise)
- Label directly on slices — eliminate the legend and its lookup cost
- Group small categories as "Other" rather than showing many tiny slivers
- No 3D effects, no exploding slices — both distort perceived area
- Donut charts work the same as pies; the center hole can hold a key metric or label

## Anti-patterns

- More than 5 slices — switch to a horizontal bar chart for clearer ranking
- Slices that don't sum to 100% — this is definitionally wrong for a part-to-whole chart
- 3D rendering — rotates the chart plane and makes back slices appear smaller than they are
- Exploding one slice — draws attention but distorts all size comparisons

→ [Storytelling with Data: What is a pie chart?](https://www.storytellingwithdata.com/blog/2020/5/14/what-is-a-pie-chart)
