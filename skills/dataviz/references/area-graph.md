# Area Graph

**Use when**: rise/fall over time where the filled volume adds meaning (total quantity); stacked area for part-to-whole proportions over time with one dominant component.  
**Avoid when**: multiple volatile series will overlap and obscure each other; non-zero-referenced scale; fine distinctions between values matter (area is harder to judge than line position).

## Key rules

- Zero baseline is **mandatory** — area encoding breaks without it (unlike line graphs)
- Prefer one series; for stacked, keep to ≤ 4–5 bands
- Use semi-transparent fills when series overlap to reveal hidden data
- Order series by stability — the most volatile series at the top, most stable at the bottom
- Direct-label bands at the right edge; avoid relying on a legend

## Anti-patterns

- Area graph on a non-zero scale — the filled area implies a quantity that starts at zero
- Overlapping (non-stacked) areas with opaque fills — data disappears behind the front series
- Stacked area when you need to compare the middle bands — only the bottom band has a fixed baseline

→ [Storytelling with Data: What is an area graph?](https://www.storytellingwithdata.com/blog/2020/4/9/what-is-an-area-graph)
