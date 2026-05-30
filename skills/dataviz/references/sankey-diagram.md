# Sankey Diagram

**Use when**: actual directional flow exists between stages — conversion funnels, budget allocation, energy/material flows, process mapping where volumes move from node to node.  
**Avoid when**: no genuine flow exists in the data (implies causation or directionality that isn't there); precise comparisons between individual flows are needed; the diagram would have more than ~6–7 nodes per column.

## Key rules

- Flow width must be proportional to quantity — this is the primary encoding
- Label flows with actual numbers when precision matters (width alone is imprecise)
- Keep node and stage count manageable — each added column multiplies visual complexity
- Order nodes within each column to minimize crossing flows
- Color flows to trace a path through the diagram rather than just to differentiate nodes

## Anti-patterns

- Sankey for categorical data with no directional relationship — implies flow that doesn't exist
- Too many nodes per column (8+) — the diagram becomes an unreadable knot
- Relying only on visual width for precise comparisons — always label the values

→ [Storytelling with Data: What is a Sankey diagram?](https://www.storytellingwithdata.com/blog/what-is-a-sankey-diagram)
