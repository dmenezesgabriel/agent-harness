# Chart Decision Tree

Walk top-down, state the path taken, and justify the leaf node.

```
What kind of data?
│
├── NUMERIC only
│   ├── 1 variable
│   │   └── → Histogram, Density Plot
│   ├── 2 variables
│   │   ├── ordered (one is time/sequence)
│   │   │   └── → Line, Area, Connected Scatter
│   │   └── unordered
│   │       ├── few points (<2000) → Scatter, Box Plot, Violin
│   │       └── many points       → 2D Density, Hex Bin, Violin
│   ├── 3 variables
│   │   ├── ordered   → Line, Stacked Area, Streamgraph
│   │   └── unordered → Bubble, Violin, Box Plot
│   └── several variables
│       ├── ordered   → Stacked Area, Streamgraph, Heatmap, Ridgeline
│       └── unordered → Heatmap, Correlogram, PCA, Ridgeline, Box/Violin
│
├── CATEGORIC only
│   ├── 1 variable
│   │   └── → Bar, Lollipop, Pie, Donut, Treemap, Word Cloud, Waffle
│   └── 2+ variables
│       ├── nested (hierarchy: continent > country > city)
│       │   └── → Treemap, Sunburst, Dendrogram, Circular Packing
│       ├── subgroup (every combination: gender × age)
│       │   └── → Grouped Bar, Stacked Bar, Spider/Radar, Heatmap, Parallel Plot
│       ├── two independent lists (overlap)
│       │   └── → Venn Diagram
│       └── adjacency (flows between lists)
│           └── → Sankey, Chord, Arc Diagram, Network
│
├── NUMERIC + CATEGORIC (mixed)
│   ├── one observation per group
│   │   ├── 1 numeric
│   │   │   └── → Bar, Lollipop, Pie, Donut, Treemap
│   │   └── several numerics
│   │       ├── one numeric is ordered → Line, Area, Stacked Area, Streamgraph
│   │       └── none ordered          → Grouped Bar, Stacked Bar, Heatmap, Spider, Parallel
│   └── several observations per group (distributions)
│       └── → Violin, Box Plot, Ridgeline, Density, Histogram
│
├── TIME SERIES
│   ├── 1 series  → Bar, Lollipop, Line, Area, Ridgeline, Box/Violin
│   └── several series
│       ├── few (<7)  → Multi-line, Stacked Area, Streamgraph
│       └── many      → Heatmap, Ridgeline, Small Multiples
│
├── GEOGRAPHIC
│   ├── points (lat/lon)     → Bubble Map, Hex Bin Map, Connection Map
│   ├── regions (boundaries) → Choropleth Map
│   └── structure only       → Basic Map
│
└── NETWORK / RELATIONAL
    ├── non-hierarchical
    │   └── → Network, Hive Plot, Heatmap (adj. matrix), Sankey, Arc/Chord
    └── hierarchical (parent → child)
        ├── values on edges  → Chord, Sankey, Dendrogram, Edge Bundling
        ├── values on leaves → Treemap, Sunburst, Circular Packing, Sankey, Dendrogram
        └── structure only   → Dendrogram, Sunburst, Circular Packing, Treemap
```
