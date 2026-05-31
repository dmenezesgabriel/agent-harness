import re
from typing import Protocol

from behave import given, then


class ChartContext(Protocol):
    artifacts: dict[str, str]
    current_file: str
    current_content: str


# Hex values that are perceptually "red" or "green" to the trichromat eye
# but collapse to the same gray under deuteranopia — the most common colorblindness.
_RED_HEX = frozenset({"#d62728", "#ff0000", "#ee0000", "#cc0000", "#e41a1c", "#c0392b"})
_GREEN_HEX = frozenset(
    {"#2ca02c", "#00ff00", "#00ee00", "#00cc00", "#4daf4a", "#27ae60"}
)
_ALL_HEX_PAT = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
_RED_NAME_PAT = re.compile(r'"(?:red|crimson|firebrick)"', re.IGNORECASE)
_GREEN_NAME_PAT = re.compile(r'"(?:green|lime|forestgreen|darkgreen)"', re.IGNORECASE)

# Patterns that signal 3D rendering — Chart.js, ECharts, Plotly, Matplotlib
_3D_PATTERNS = [
    r"type:\s*['\"]3d['\"]",
    r"type:\s*['\"]scatter3d['\"]",
    r"type:\s*['\"]surface['\"]",
    r'"3D"',
    r"perspective\s*:",
    r"gl3d",
    r"go\.Scatter3d\b",  # Plotly Python
    r"go\.Surface\b",  # Plotly Python
    r"mpl_toolkits\.mplot3d",  # Matplotlib
    r"\bAxes3D\b",  # Matplotlib
]

# Patterns that signal dual y-axes — Chart.js, ECharts, Plotly, Matplotlib, Recharts
_DUAL_Y_PATTERNS = [
    r"yAxis2",  # ECharts / Highcharts
    r"y2\s*:",  # various
    r"yAxisID\s*:\s*['\"]y2['\"]",  # Chart.js
    r"axis\s*:\s*['\"]y2['\"]",  # Chart.js
    r"secondary_y\s*=\s*True",  # Plotly Python
    r"\.twinx\(\)",  # Matplotlib
    r'"yaxis2"\s*:',  # Plotly JSON
    r"<YAxis[^>]*orientation\s*=\s*['\"]right['\"]",  # Recharts second Y axis
]

# non-zero y minimum — Chart.js `min:`, Vega-Lite `domainMin`, Matplotlib `set_ylim`/`ylim`
_NONZERO_Y_MIN = re.compile(
    r"(?:^|\W)min\s*:\s*([1-9]\d*(?:\.\d+)?)"
    r"|domainMin\s*:\s*([1-9]\d*)"
    r"|set_ylim\s*\(\s*([1-9]\d*)"
    r"|ylim\s*=\s*\(\s*([1-9]\d*)"
)

_CHART_TYPE = re.compile(r"""type\s*:\s*["'](\w+)["']""")
# JSX component name → chart type (Recharts, Victory, Nivo, …)
_JSX_CHART_COMPONENT = re.compile(
    r"<(Line|Bar|Area|Pie|Scatter|Radar|Bubble|Donut)Chart[\s/>]", re.IGNORECASE
)
_LABELS_ARRAY = re.compile(r"labels\s*:\s*\[([^\]]+)\]")
# ISO date strings like "2024-01-01" signal time-series data
_ISO_DATE_LABEL = re.compile(r'"\d{4}-\d{2}-\d{2}"')
# Explicit series color — Chart.js backgroundColor or JSX stroke/fill/color props
_BACKGROUND_COLOR_VALUE = re.compile(
    r"backgroundColor\s*:\s*"
    r'(?:["\'](?:#[0-9a-fA-F]{3,8}|rgba?\([^)]+\)|hsla?\([^)]+\)|[a-z]+)["\']|\[)'
    r'|(?:stroke|fill|color)\s*=\s*["\']#[0-9a-fA-F]{3,8}["\']',
    re.IGNORECASE,
)
# Captures all items inside backgroundColor: [...]
_BACKGROUND_COLORS_ARRAY = re.compile(r"backgroundColor\s*:\s*\[([^\]]+)\]", re.DOTALL)
_RECOGNIZED_CHART_TYPES = frozenset(
    {"bar", "line", "pie", "doughnut", "scatter", "bubble", "radar"}
)

# Keywords that identify a file as containing a visualization — any framework
_VIZ_KEYWORDS = re.compile(
    r"new\s+Chart\b|Chart\.js"  # Chart.js
    r"|plotly|go\.Figure|go\.\w+Trace|px\.\w+\("  # Plotly
    r"|alt\.Chart\b|\.mark_line\(\)|\.mark_bar\(\)"  # Altair
    r"|import\s+matplotlib|plt\.(plot|bar|scatter|hist|show)\b"  # Matplotlib
    r'|"mark"\s*:\s*"(?:line|bar|area|point|circle)"'  # Vega-Lite
    r"|d3\.select\b"  # D3.js
    r"|from\s+['\"](?:recharts|victory|echarts|highcharts|apexcharts|@nivo/\w+)['\"]"  # React libs
    r"|(?:LineChart|BarChart|AreaChart|PieChart|ScatterChart)\b",  # Recharts components
    re.IGNORECASE,
)

# File extensions that can carry a visualization, in preference order
_VIZ_EXTENSIONS = (".html", ".js", ".jsx", ".tsx", ".py", ".ipynb", ".json")


@given("the dataviz artifact set is loaded")
def step_artifact_set_loaded(context: ChartContext) -> None:
    assert hasattr(context, "artifacts"), "artifacts not set — check environment.py"
    assert context.artifacts, "artifact set is empty — no fixture files found"


@given('the chart artifact "{filename}"')
def step_load_chart_artifact(context: ChartContext, filename: str) -> None:
    content = context.artifacts.get(filename)
    assert content is not None, (
        f"Chart artifact {filename!r} not found; available: {sorted(context.artifacts)}"
    )
    context.current_file = filename
    context.current_content = content


@then("the chart does not have a non-zero y-axis minimum")
def step_no_nonzero_y_min(context: ChartContext) -> None:
    match = _NONZERO_Y_MIN.search(context.current_content)
    assert not match, (
        f"{context.current_file!r} sets a non-zero y-axis min ({match.group(0).strip()}); "
        "bar and area charts must start at zero"
    )


@then("the chart has a non-zero y-axis minimum")
def step_has_nonzero_y_min(context: ChartContext) -> None:
    match = _NONZERO_Y_MIN.search(context.current_content)
    assert match, (
        f"{context.current_file!r} does not set a non-zero y-axis min; "
        "expected the negative fixture to have one"
    )


@then("the chart does not use 3D rendering")
def step_no_3d(context: ChartContext) -> None:
    _assert_none_match(
        context.current_content, _3D_PATTERNS, context.current_file, "3D rendering"
    )


@then("the artifact does not contain 3D keywords")
def step_no_3d_keywords(context: ChartContext) -> None:
    _assert_none_match(
        context.current_content, _3D_PATTERNS, context.current_file, "3D keywords"
    )


@then("the chart does not use dual y-axes")
def step_no_dual_y(context: ChartContext) -> None:
    _assert_none_match(
        context.current_content, _DUAL_Y_PATTERNS, context.current_file, "dual y-axis"
    )


@then("the artifact does not contain dual y-axis keywords")
def step_no_dual_y_keywords(context: ChartContext) -> None:
    _assert_none_match(
        context.current_content, _DUAL_Y_PATTERNS, context.current_file, "dual y-axis"
    )


@then("the pie chart exceeds 5 slices")
def step_pie_exceeds_5_slices(context: ChartContext) -> None:
    count = _count_pie_slices(context.current_content)
    assert count > 5, (
        f"{context.current_file!r} has {count} pie slice(s); "
        "expected more than 5 for the negative fixture"
    )


@then("the pie chart has at most 5 slices")
def step_pie_at_most_5_slices(context: ChartContext) -> None:
    count = _count_pie_slices(context.current_content)
    assert count <= 5, (
        f"{context.current_file!r} has {count} pie slice(s); "
        "maximum is 5 (use a bar chart or table for more categories)"
    )


@then("the artifact set contains a chart artifact")
def step_has_chart_artifact(context: ChartContext) -> None:
    """Skill must produce any file (HTML, JS, Python, notebook, JSON) containing a visualization."""
    chart_files = [
        k
        for k, v in context.artifacts.items()
        if any(k.endswith(ext) for ext in _VIZ_EXTENSIONS) and _VIZ_KEYWORDS.search(v)
    ]
    has_chart_in_output = bool(
        _VIZ_KEYWORDS.search(context.artifacts.get("output.txt", ""))
    )
    assert chart_files or has_chart_in_output, (
        f"Skill produced no chart artifacts; got: {sorted(context.artifacts)}"
    )


@given("the live chart artifact")
def step_load_live_artifact(context: ChartContext) -> None:
    """Load the primary visualization file regardless of framework or extension."""
    for ext in _VIZ_EXTENSIONS:
        candidates = sorted(
            k
            for k, v in context.artifacts.items()
            if k.endswith(ext) and _VIZ_KEYWORDS.search(v)
        )
        if candidates:
            context.current_file = candidates[0]
            context.current_content = context.artifacts[candidates[0]]
            return
    if "output.txt" in context.artifacts:
        context.current_file = "output.txt"
        context.current_content = context.artifacts["output.txt"]
        return
    raise AssertionError(
        f"No chart artifact found in live output; available: {sorted(context.artifacts)}"
    )


@then("the chart type is appropriate for its labels")
def step_chart_type_appropriate(context: ChartContext) -> None:
    """Chart type must be recognized, and bar must not be used for ISO-date time series.

    Supports Chart.js (`type: "line"`) and JSX-component libs (<LineChart>, <BarChart>, …).
    """
    content = context.current_content

    # Chart.js: type: "..."
    type_match = _CHART_TYPE.search(content)
    if type_match:
        chart_type = type_match.group(1)
        assert chart_type in _RECOGNIZED_CHART_TYPES, (
            f"{context.current_file!r}: unrecognized chart type {chart_type!r}; "
            f"must be one of {sorted(_RECOGNIZED_CHART_TYPES)}"
        )
        labels_match = _LABELS_ARRAY.search(content)
        if chart_type == "bar" and labels_match:
            assert not _ISO_DATE_LABEL.search(labels_match.group(1)), (
                f"{context.current_file!r}: bar chart used with ISO date labels — "
                "use a line chart for continuous time series"
            )
        return

    # JSX component libs (Recharts, Victory, Nivo, …): <LineChart>, <BarChart>, …
    jsx_match = _JSX_CHART_COMPONENT.search(content)
    assert jsx_match, (
        f"{context.current_file!r} has no recognizable chart type — "
        "expected `type: '...'` (Chart.js) or a JSX chart component (<LineChart>, <BarChart>, …)"
    )


@then("the chart has a bar type with ISO date labels")
def step_bar_with_iso_dates(context: ChartContext) -> None:
    """Assert the negative fixture has the bar+ISO-date mismatch."""
    type_match = _CHART_TYPE.search(context.current_content)
    assert type_match and type_match.group(1) == "bar", (
        f"{context.current_file!r}: expected type 'bar'"
    )
    labels_match = _LABELS_ARRAY.search(context.current_content)
    assert labels_match and _ISO_DATE_LABEL.search(labels_match.group(1)), (
        f"{context.current_file!r}: expected ISO date labels in the bar chart fixture"
    )


@then("the chart has an explicit background color")
def step_explicit_background_color(context: ChartContext) -> None:
    """backgroundColor must be a valid color value — not missing or a bare variable."""
    assert _BACKGROUND_COLOR_VALUE.search(context.current_content), (
        f"{context.current_file!r} does not set a valid backgroundColor; "
        "use an explicit hex (#4e79a7), rgb(), or named color"
    )


@then("the chart uses at most 7 distinct colors")
def step_at_most_7_colors(context: ChartContext) -> None:
    """More than 7 colors in a single chart overwhelms the viewer."""
    array_match = _BACKGROUND_COLORS_ARRAY.search(context.current_content)
    if not array_match:
        return  # single color string is always ≤ 7
    colors = [c.strip() for c in array_match.group(1).split(",") if c.strip()]
    assert len(colors) <= 7, (
        f"{context.current_file!r} uses {len(colors)} colors; "
        "maximum is 7 — split into multiple charts or aggregate categories"
    )


@then("the chart exceeds 7 background colors")
def step_exceeds_7_colors(context: ChartContext) -> None:
    """Assert the negative fixture has more than 7 colors."""
    array_match = _BACKGROUND_COLORS_ARRAY.search(context.current_content)
    assert array_match, f"{context.current_file!r} has no backgroundColor array"
    colors = [c.strip() for c in array_match.group(1).split(",") if c.strip()]
    assert len(colors) > 7, (
        f"{context.current_file!r} has {len(colors)} colors; expected >7 for negative fixture"
    )


@then("the chart does not use a red-green color pair")
def step_no_red_green_pair(context: ChartContext) -> None:
    """Fail if the artifact uses both a red-ish and green-ish color — invisible under deuteranopia."""
    content = context.current_content
    found_hex = {m.group(0).lower() for m in _ALL_HEX_PAT.finditer(content)}
    has_red = bool(found_hex & _RED_HEX) or bool(_RED_NAME_PAT.search(content))
    has_green = bool(found_hex & _GREEN_HEX) or bool(_GREEN_NAME_PAT.search(content))
    assert not (has_red and has_green), (
        f"{context.current_file!r} pairs red and green series colors — "
        "indistinguishable under deuteranopia. Use the Wong palette: "
        "#0072B2 (blue) · #E69F00 (orange) · #009E73 (teal) · #CC79A7 (mauve)"
    )


@then("the chart has a red-green color pair")
def step_has_red_green_pair(context: ChartContext) -> None:
    """Assert the negative fixture has the red+green colorblind failure."""
    content = context.current_content
    found_hex = {m.group(0).lower() for m in _ALL_HEX_PAT.finditer(content)}
    has_red = bool(found_hex & _RED_HEX) or bool(_RED_NAME_PAT.search(content))
    has_green = bool(found_hex & _GREEN_HEX) or bool(_GREEN_NAME_PAT.search(content))
    assert has_red and has_green, (
        f"{context.current_file!r} does not contain a red+green pair — "
        "expected for the negative colorblind fixture"
    )


# ── helpers ──────────────────────────────────────────────────────────────────


def _assert_none_match(
    content: str, patterns: list[str], filename: str, label: str
) -> None:
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            raise AssertionError(
                f"{filename!r} contains {label} pattern {pattern!r} "
                f"(matched: {match.group(0)!r})"
            )


def _count_pie_slices(content: str) -> int:
    """Count entries in the data array of a Chart.js pie/doughnut chart."""
    # Match: data: [n, n, n, ...]
    match = re.search(r"data\s*:\s*\[([^\]]+)\]", content)
    if not match:
        return 0
    entries = [e.strip() for e in match.group(1).split(",") if e.strip()]
    return len(entries)
