---
name: dataviz
description: >
  Guides the entire data visualization lifecycle: understanding the story, inspecting data, selecting charts, building dashboards, and iterating on design. Use when the user wants to visualize, chart, graph, plot, or dashboard their data — even if they don't explicitly say "visualization" or "dashboard". Use for chart type selection, color palette choices, visual encoding, layout design, and implementation. Also use when the user has a data file and wants insights shown visually. Handles local files (CSV, Parquet, JSON, Excel, DuckDB) via Python + DuckDB and outputs a Vite app or Jupyter notebook.
compatibility: Designed for Claude Code. Requires Python 3.11+, uv, and DuckDB. Local Vite output requires Node.js.
metadata:
  domain: data-visualization
  version: "1.1"
---

Build effective, well-designed dashboards from data. Follow the phases in order: understand the story first, inspect the data, then build.

Do not start generating charts immediately. Do not pick a chart type before inspecting the data.

## When NOT to use this skill

- The user wants exploratory data analysis without any visualization output.
- The user has a working chart and only needs a code fix or styling tweak — handle it directly.
- The data source is a live database the user cannot export — this skill targets local files.
- The user wants a static infographic in a design tool (Figma, Illustrator) with no code output.

## Core workflow

1. **Phase 0 — Environment**: Confirm data location and output format. Verify runtime dependencies.
2. **Phase 1 — Story**: Ask the four story questions one at a time. Summarize back before proceeding.
3. **Phase 2 — Data**: Request the file path. Inspect with DuckDB. Present shape, types, quality findings.
4. **Phase 3 — Chart selection**: Walk the decision tree for every chart. Present a plan table and get approval.
5. **Phase 4 — Build**: Apply F-pattern layout and design rules. Ask for theme before generating code.
6. **Phase 5 — Review**: Run the review checklist with the user. Make targeted adjustments only.
7. **Interactivity**: Suggest 1–2 global filters once the base dashboard is solid.

---

## Phase 0: Environment

Ask:

> **Where does your data live, and what output format do you need?**
>
> - **Local files** (CSV, Parquet, JSON, Excel, local DuckDB) + **Vite app** → Python + DuckDB for inspection, then a local Vite app
> - **Local files** + **Jupyter notebook** → Python + DuckDB + matplotlib/plotly inline

Remember the chosen mode — it governs data inspection (Phase 2) and code generation (Phase 4).

---

## Phase 1: The Story

Ask these four questions **one at a time**. Do not proceed until all are answered.

**Q1 — Audience**: Who is this dashboard for? (policy maker, CEO, engineers, general public — shapes level of detail and language)

**Q2 — Decision**: What decision should this help someone make? Give a concrete example: "Should we invest more in region X?", "Is our air quality improving?"

**Q3 — Key takeaway**: If someone looks for 5 seconds, what is the ONE thing they walk away with? Not three things — one.

**Q4 — Questions**: What 2–5 specific sub-questions should the dashboard answer?

Once all four are answered, summarize back:

```
Here's what I understand:
- Audience: [...]
- Decision: [...]
- Key takeaway: [...]
- Questions: [...]

Does this look right? I'll use this to guide every chart choice and design decision.
```

---

## Phase 2: The Data

Ask for the table name or file path. Inspect using `uv run python`:

```python
import duckdb
con = duckdb.connect()
print(con.execute("SELECT * FROM '[path]' LIMIT 5").df())
print(con.execute("DESCRIBE SELECT * FROM '[path]'").df())
print(con.execute("SELECT COUNT(*) FROM '[path]'").fetchone())
```

Present findings before proceeding:

```
Here's what I found:
- [X] rows, [Y] columns
- Key columns: [list with types]
- Time column: [name, range, granularity — if any]
- Categorical columns: [name, cardinality]
- Numeric columns: [name, range, distribution notes]
- Data quality: [nulls, outliers, surprises]

Based on your questions and this data shape, here's my chart plan:
```

---

## Phase 3: Chart Selection

For every chart, walk this tree top-down, state the path taken, and justify the leaf node.

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

For each chart type identified in the tree, read its reference file before finalizing the plan:

| Chart type | Reference file |
|---|---|
| Bar chart | [bar-chart.md](references/bar-chart.md) |
| Line graph | [line-graph.md](references/line-graph.md) |
| Area graph | [area-graph.md](references/area-graph.md) |
| Stacked bar | [stacked-bar.md](references/stacked-bar.md) |
| Pie / Donut | [pie-chart.md](references/pie-chart.md) |
| Scatterplot | [scatterplot.md](references/scatterplot.md) |
| Bubble chart | [bubble-chart.md](references/bubble-chart.md) |
| Box plot | [boxplot.md](references/boxplot.md) |
| Dot plot | [dot-plot.md](references/dot-plot.md) |
| Slopegraph | [slopegraph.md](references/slopegraph.md) |
| Waterfall | [waterfall-chart.md](references/waterfall-chart.md) |
| Treemap | [treemap.md](references/treemap.md) |
| Sankey diagram | [sankey-diagram.md](references/sankey-diagram.md) |
| Spider / radar | [spider-chart.md](references/spider-chart.md) |
| Bullet graph | [bullet-graph.md](references/bullet-graph.md) |
| Choropleth map | [choropleth-map.md](references/choropleth-map.md) |
| Table | [table.md](references/table.md) |
| Flowchart | [flowchart.md](references/flowchart.md) |
| Gantt chart | [gantt-chart.md](references/gantt-chart.md) |
| Square area / unit chart | [square-area-unit-chart.md](references/square-area-unit-chart.md) |

Present the chart plan as a table:

```
| Your question | Data path in tree | Chart type | Why |
|--------------|-------------------|-----------|-----|
| "Is PM2.5 improving?" | Time series → 1 series | Line chart | ordered time axis, single metric |
| "Which regions are worst?" | Numeric + Categoric → 1 obs/group → 1 numeric | Horizontal bar | categorical ranking |
```

Ask: **"Does this chart plan make sense? Want to change anything before I build?"**

---

## Phase 4: Build the Dashboard

### Layout (F-pattern)

1. Title + subtitle — the key takeaway as a sentence
2. KPI cards — headline numbers in a row
3. Primary chart — most important trend (top-left, largest)
4. Supporting charts — comparisons and breakdowns
5. Detail table — exact numbers for drill-down

### Design rules (apply automatically)

- **Data-ink ratio**: Remove borders, shadows, excessive gridlines. Light gray horizontal gridlines only.
- **Color**: Colors must be perceptually distinct for users with deuteranopia and protanopia (the most common colorblindness types). Two well-tested defaults:
  - Wong (2011): `#0072B2` · `#E69F00` · `#009E73` · `#CC79A7` · `#56B4E9` · `#F0E442` · `#D55E00`
  - Okabe & Ito: `#E69F00` · `#56B4E9` · `#009E73` · `#F0E442` · `#0072B2` · `#D55E00` · `#CC79A7`
  For brand or custom palettes, verify at [Viz Palette](https://projects.susielu.com/viz-palette).
  Never pair pure red with pure green — indistinguishable under deuteranopia.
  Max 7 colors. Same color = same meaning across all charts.
- **Reference lines**: Add thresholds, benchmarks, or guidelines where relevant.
- **Context**: Include data source and time period as a footnote.
- **Labels**: Direct labeling over legends when possible. Round to meaningful precision.

### Narrative structure

- Section headers tell the story, not describe the chart ("Regional disparities" not "Bar chart of regions")
- Flow: context → tension → insight → action

### Ask before generating code

> **Do you have a brand or theme preference?**
>
> - "Tufte minimal" — maximum data-ink ratio, almost no decoration
> - "Financial Times" — salmon background, authoritative serif headers
> - "Dark mode" — dark background, bright accents, high contrast
> - "Clean analytical" — white background, sans-serif, institutional clarity
>
> Or give me hex values and I'll match your brand.

---

## Phase 5: Review & Iterate

Run through this checklist with the user:

- [ ] Can someone understand the main takeaway in 5 seconds?
- [ ] Does every chart answer a specific question from Phase 1?
- [ ] Is there a clear visual hierarchy (not everything screaming for attention)?
- [ ] Would it still work printed in grayscale?
- [ ] Are reference lines and data sources included?
- [ ] Is the color palette consistent and meaningful?
- [ ] Does the narrative flow top-to-bottom (context → insight → action)?

Ask: **"How does this look? What would you change?"**

Iterate based on feedback. Make targeted adjustments — do not regenerate everything.

---

## Interactivity (suggest proactively after Phase 5)

> **Want to add interactivity?**
>
> - **Cross-filtering** — click a bar/region to filter all other charts
> - **Time range filter** — toggle between periods or use a slider
> - **Metric toggle** — switch between different measures
>
> I'll keep it to 1–2 global filters. No dropdown overload.

---

## Gotchas

- **DuckDB file paths in SQL**: Always wrap paths in single quotes: `SELECT * FROM 'path/to/file.csv'`. Unquoted paths fail silently or produce confusing errors.
- **Excel files**: DuckDB requires the `spatial` or `excel` extension for `.xlsx`. Prefer converting to CSV first if the user can.
- **Parquet schema drift**: If multiple Parquet files have different schemas, use `read_parquet(['a.parquet', 'b.parquet'], union_by_name=True)` to avoid column mismatch errors.
- **Date columns parsed as strings**: DuckDB infers dates from CSVs, but formats like `MM/DD/YYYY` are read as strings. Cast explicitly: `CAST(date_col AS DATE)` after confirming the format.
- **Vite port conflicts**: If port 5173 is in use, Vite auto-increments to 5174. Tell the user to check the terminal output for the actual URL.
- **Large CSVs and DuckDB LIMIT**: `LIMIT 5` on a remote file still downloads the whole file. For large remote files, use DuckDB's `read_csv_auto` with `sample_size` instead.

## Anti-patterns to avoid

- **Pie charts with more than 5 slices** → use bar or table
- **3D charts of any kind** → always 2D
- **Dual y-axes with unrelated metrics** → use separate charts
- **Line charts with more than 7 series** → use small multiples
- **Truncated y-axes on bar charts** → always start at zero
- **Area charts without a zero baseline** → area encoding breaks; zero baseline is mandatory
- **Stacked bars when subcomponent comparison is the goal** → only the baseline segment has an aligned axis; use grouped bars or separate charts
- **Slopegraph for more than two time points** → middle data gets lost; use a line chart instead
- **Bubble chart when bubble sizes cluster similarly** → the 3rd dimension adds noise, not insight; use scatter instead
- **Treemap with zero or negative values** → area encoding can't represent these; use bar chart
- **Waterfall with extreme scale disparities** → large base value + tiny changes makes bars invisible; show only deltas with text for the base
- **Table during a live presentation** → audience can't listen and read simultaneously; use chart + annotations
- **Boxplot without explaining the structure** → non-technical audiences are lost; narrate each component before revealing the full chart
- **Rainbow palettes with no semantic meaning** → use intentional palettes
- **Generating charts before inspecting data** → always run Phase 2 first
- **Skipping the story questions** → every chart choice must trace back to a question from Phase 1

## Before marking complete

- [ ] Story questions answered and summary confirmed by user
- [ ] Data inspected — shape, types, and quality findings presented before charting
- [ ] Chart plan approved before build started
- [ ] Every chart answers a specific question from Phase 1
- [ ] Color palette is accessible: explicit hardcoded colors, no red+green pairing, verified for deuteranopia
- [ ] Data source and time period noted in the dashboard
- [ ] Phase 5 review checklist run with user

## Final response

After delivering the dashboard, summarize:

- Output location (file path or URL)
- Charts built and which Phase 1 question each answers
- Data quality issues found, if any
- Design choices made (theme, palette, any layout deviations)
- Interactivity added, if any
- Open follow-up items, if any

## Reference: Color tools

- [Colorbrewer 2.0](https://colorbrewer2.org/) — colorblind-safe sequential/diverging/qualitative palettes
- [Viz Palette](https://projects.susielu.com/viz-palette) — test your palette for colorblind accessibility

## Reference: Chart decision frameworks

- [From Data to Viz](https://www.data-to-viz.com/) — full decision tree with 38 chart types
- [FT Visual Vocabulary](https://ft.com/vocabulary) — 9 data relationships mapped to chart types
- [The Graphic Continuum](https://policyviz.com/2014/09/09/graphic-continuum/) — 90+ chart types by complexity
