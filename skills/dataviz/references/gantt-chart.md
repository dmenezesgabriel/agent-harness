# Gantt Chart

**Use when**: visualizing project timelines, task scheduling, and dependencies — when duration and sequencing of work items are the core message.  
**Avoid when**: the data is not time-based; you only need to show milestones (a timeline or dot plot on a time axis is simpler); the number of tasks exceeds ~20–30 rows (becomes unreadable without interactivity).

## Key rules

- Sort tasks by start date or by critical path order — not alphabetically
- Highlight the critical path (the sequence that determines total project duration) with a distinct color or weight
- Show dependencies explicitly with arrows between dependent tasks
- Use a consistent time scale on the x-axis; include today's date as a reference line
- For status tracking, use color to encode completion state (done / in-progress / not started)

## Anti-patterns

- Gantt chart without dependency arrows — the sequence looks arbitrary
- Too many tasks without grouping by phase or workstream — the chart becomes a wall of bars
- No current-date reference line — readers can't tell where the project stands relative to now

→ [Storytelling with Data: What is a Gantt chart?](https://www.storytellingwithdata.com/blog/what-is-a-gantt-chart)
