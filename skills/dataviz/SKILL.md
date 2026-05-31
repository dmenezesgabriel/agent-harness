---
name: dataviz
description: >
  Guides the full visualization lifecycle: story → inspect → select → build → review. Use when the user wants to visualize, chart, graph, plot, or dashboard data — including when they say "show me trends", "compare these categories", "make this data presentable", "tell a story with data", or "I have a file and want to understand it visually". Handles local files (CSV, Parquet, JSON, Excel, DuckDB) via Python + DuckDB; outputs Vite app or Jupyter notebook.
metadata:
  domain: data-visualization
  version: "1.3"
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

Ask: **Where does your data live, and what output format do you need?**

- **Vite app**: local files → Python + DuckDB inspection → Vite app
- **Notebook**: local files → Python + DuckDB + matplotlib/plotly inline

Remember the mode — it governs Phase 2 (inspection) and Phase 4 (code generation).

---

## Phase 1: The Story

Ask **one at a time**; do not proceed until all four are answered.

**Q1 — Audience**: Who is this for? (shapes detail level and language)

**Q2 — Decision**: What decision does it support? Give a concrete example.

**Q3 — Key takeaway**: If someone looks for 5 seconds, what is the ONE thing they walk away with?

**Q4 — Questions**: What 2–5 specific sub-questions should it answer?

Summarize back:

```
Here's what I understand:
- Audience: [...]
- Decision: [...]
- Key takeaway: [...]
- Questions: [...]

Does this look right? I'll use this to guide every chart choice and design decision.
```

Example:
- Audience: city council members
- Decision: whether to expand bike lanes in high-accident corridors
- Key takeaway: three corridors account for 70% of cyclist injuries
- Questions: Which corridors are worst? Trend over 3 years? Peak hours?

---

## Phase 2: The Data

Ask for the table name or file path. Inspect using the bundled script:

```sh
uv run scripts/inspect_data.py '[path]'
```

Present findings before proceeding:

```txt
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

Read [decision-tree.md](references/decision-tree.md) and walk it top-down for every chart. State the path taken and justify the leaf node.

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

**Default stack**: Vite app → Chart.js (CDN). Notebook → matplotlib or Plotly. Use what the user requests if they name a library; otherwise stick to the default.

### Layout (F-pattern)

1. Title + subtitle — the key takeaway as a sentence
2. KPI cards — headline numbers in a row
3. Primary chart — most important trend (top-left, largest)
4. Supporting charts — comparisons and breakdowns
5. Detail table — exact numbers for drill-down

### Design rules (apply automatically)

- **Data-ink ratio**: Remove borders, shadows, excessive gridlines. Light gray horizontal gridlines only.
- **Color**: Colorblind-safe defaults (deuteranopia/protanopia):
  - Wong: `#0072B2` `#E69F00` `#009E73` `#CC79A7` `#56B4E9` `#F0E442` `#D55E00`
  - Okabe & Ito: `#E69F00` `#56B4E9` `#009E73` `#F0E442` `#0072B2` `#D55E00` `#CC79A7`
  Custom palettes: verify at [Viz Palette](https://projects.susielu.com/viz-palette). Max 7 colors. Never pure red + pure green. Same color = same meaning across all charts.
- **Reference lines**: Add thresholds, benchmarks, or guidelines where relevant.
- **Context**: Include data source and time period as a footnote.
- **Labels**: Direct labeling over legends when possible. Round to meaningful precision.

### Narrative structure

- Section headers tell the story, not describe the chart ("Regional disparities" not "Bar chart of regions")
- Flow: context → tension → insight → action

### Ask before generating code

**Do you have a brand or theme preference?**
- Tufte minimal — maximum data-ink ratio, almost no decoration
- Financial Times — salmon background, authoritative serif headers
- Dark mode — dark background, bright accents, high contrast
- Clean analytical — white background, sans-serif, institutional clarity
- Or provide hex values to match your brand.

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

**Want to add interactivity?**
- Cross-filtering — click a bar/region to filter all other charts
- Time range filter — toggle between periods or use a slider
- Metric toggle — switch between different measures

Limit to 1–2 global filters. No dropdown overload.

---

## Gotchas

- **DuckDB file paths in SQL**: Always wrap paths in single quotes: `SELECT * FROM 'path/to/file.csv'`. Unquoted paths fail silently.
- **Excel files**: DuckDB requires the `spatial` or `excel` extension for `.xlsx`. Prefer converting to CSV first.
- **Parquet schema drift**: Use `read_parquet(['a.parquet', 'b.parquet'], union_by_name=True)` when files have different schemas.
- **Date columns parsed as strings**: Formats like `MM/DD/YYYY` are read as strings. Cast explicitly: `CAST(date_col AS DATE)`.
- **Vite port conflicts**: If 5173 is in use, Vite auto-increments. Check terminal output for the actual URL.
- **Large CSVs and DuckDB LIMIT**: `LIMIT 5` on a remote file still downloads the whole file. Use `read_csv_auto` with `sample_size` instead.

## Anti-patterns to avoid

- **Generating charts before inspecting data** → always run Phase 2 first
- **Skipping the story questions** → every chart choice must trace back to a question from Phase 1
- **Dual y-axes with unrelated metrics** → use separate charts

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
