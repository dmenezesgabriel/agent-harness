"""Shared step definitions for all skill features.

Steps work directly against the filesystem in context.ws (the reconstructed
workspace directory). This means assertions are about what the agent actually
did — not what it said it would do.
"""
import json
import re
from pathlib import Path

from behave import given, then


# ── Background ────────────────────────────────────────────────────────────────

@given("the agent has run in the workspace")
def step_workspace_ready(context):
    assert context.ws.is_dir(), f"Workspace not found: {context.ws}"


# ── Directory existence ───────────────────────────────────────────────────────

@then('the directory "{dirname}" exists')
def step_dir_exists(context, dirname):
    target = context.ws / dirname
    assert target.is_dir(), (
        f"Expected directory '{dirname}' in workspace but it was not created.\n"
        f"Workspace contents: {[str(p.relative_to(context.ws)) for p in context.ws.rglob('*')]}"
    )


@then('if directory "{dirname}" exists, it contains only "{ext}" files')
def step_dir_only_ext(context, dirname, ext):
    target = context.ws / dirname
    if not target.is_dir():
        return  # optional directory — pass vacuously
    bad = [p for p in target.iterdir() if p.is_file() and p.suffix != ext]
    assert not bad, f"Non-{ext} files found in {dirname}/: {bad}"


# ── File existence ────────────────────────────────────────────────────────────

@then('at least {n:d} file matching "{pattern}" exists')
def step_at_least_n_files(context, n, pattern):
    files = sorted(context.ws.glob(pattern))
    assert len(files) >= n, (
        f"Expected >= {n} file(s) matching '{pattern}', found {len(files)}.\n"
        f"Workspace contents: {[str(p.relative_to(context.ws)) for p in context.ws.rglob('*') if p.is_file()]}"
    )


@then('fewer than {n:d} file matching "{pattern}" exists')
def step_fewer_than_n_files(context, n, pattern):
    files = sorted(context.ws.glob(pattern))
    assert len(files) < n, (
        f"Expected < {n} file(s) matching '{pattern}', found {len(files)}: {files}"
    )


@then('no file matching "{pattern}" exists at the workspace root')
def step_no_root_md(context, pattern):
    files = list(context.ws.glob(pattern))
    assert not files, (
        f"Agent wrote {pattern} files at workspace root (should be inside a subdirectory): {files}"
    )


@then('the file "{filepath}" exists')
def step_file_exists(context, filepath):
    target = context.ws / filepath
    assert target.is_file(), (
        f"Expected file '{filepath}' in workspace but it was not created.\n"
        f"Workspace contents: {[str(p.relative_to(context.ws)) for p in context.ws.rglob('*') if p.is_file()]}"
    )


@then('the file "{filepath}" does not exist')
def step_file_not_exists(context, filepath):
    target = context.ws / filepath
    assert not target.exists(), f"File '{filepath}' exists but should not."


# ── File naming format ────────────────────────────────────────────────────────

@then('every file in "{pattern}" has a name matching "{regex}"')
def step_filenames_match_regex(context, pattern, regex):
    files = sorted(context.ws.glob(pattern))
    if not files:
        return  # vacuously true — file-existence scenarios catch missing files
    compiled = re.compile(regex)
    bad = [p.name for p in files if not compiled.match(p.name)]
    assert not bad, (
        f"File names do not match pattern '{regex}': {bad}"
    )


# ── Numeric prefix uniqueness ─────────────────────────────────────────────────

@then('all files in "{pattern}" have unique numeric prefixes')
def step_unique_numeric_prefixes(context, pattern):
    files = sorted(context.ws.glob(pattern))
    prefixes = []
    for f in files:
        m = re.match(r'^(\d+)', f.name)
        if m:
            prefixes.append(m.group(1))
    duplicates = [p for p in prefixes if prefixes.count(p) > 1]
    assert not duplicates, (
        f"Duplicate numeric prefixes found in '{pattern}': {list(set(duplicates))}"
    )


# ── Section content ───────────────────────────────────────────────────────────

def _section_has_content(text: str, section: str) -> bool:
    """Return True if a markdown heading matching section has non-empty content below it."""
    lines = text.splitlines()
    in_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and section.lower() in stripped.lower():
            in_section = True
            continue
        if in_section:
            if stripped.startswith("#"):
                break
            if stripped:
                return True
    return False


@then('every file in "{pattern}" contains non-empty section "{section}"')
def step_section_nonempty(context, pattern, section):
    files = sorted(context.ws.glob(pattern))
    if not files:
        return
    missing = []
    for f in files:
        text = f.read_text(errors="replace")
        if not _section_has_content(text, section):
            missing.append(f.name)
    assert not missing, (
        f"Section '{section}' is missing or empty in: {missing}"
    )


@then('every file in "{pattern}" contains any of "{keywords}"')
def step_contains_any_keyword(context, pattern, keywords):
    files = sorted(context.ws.glob(pattern))
    if not files:
        return
    kws = [k.strip().lower() for k in keywords.split(",")]
    missing = []
    for f in files:
        text = f.read_text(errors="replace").lower()
        if not any(kw in text for kw in kws):
            missing.append(f.name)
    assert not missing, (
        f"None of {kws} found in: {missing}"
    )


# ── Content pattern matching ──────────────────────────────────────────────────

@then('every file in "{pattern}" has content matching "{regex}"')
def step_content_matches_regex(context, pattern, regex):
    files = sorted(context.ws.glob(pattern))
    if not files:
        return  # vacuously true — file-existence scenarios catch missing files
    compiled = re.compile(regex)
    bad = [f.name for f in files if not compiled.search(f.read_text(errors="replace"))]
    assert not bad, (
        f"Regex '{regex}' not found in: {bad}\nWorkspace: {context.ws}"
    )


@then('every file in "{pattern}" has frontmatter key "{key}" with value "{value}"')
def step_frontmatter_key_value(context, pattern, key, value):
    files = sorted(context.ws.glob(pattern))
    if not files:
        return  # vacuously true
    kv_re = re.compile(rf"^{re.escape(key)}:\s*{re.escape(value)}\s*$", re.MULTILINE)
    no_fm, wrong_val = [], []
    for f in files:
        text = f.read_text(errors="replace")
        fm_match = re.match(r"^---\r?\n(.*?)\r?\n---", text, re.DOTALL)
        if not fm_match:
            no_fm.append(f.name)
        elif not kv_re.search(fm_match.group(1)):
            wrong_val.append(f.name)
    parts = []
    if no_fm:
        parts.append(f"no frontmatter block: {no_fm}")
    if wrong_val:
        parts.append(f"key '{key}' not '{value}': {wrong_val}")
    assert not parts, f"Frontmatter check failed ({context.ws}): " + "; ".join(parts)


# ── JSON validation ───────────────────────────────────────────────────────────

@then('"{filepath}" is valid JSON')
def step_valid_json(context, filepath):
    target = context.ws / filepath
    try:
        json.loads(target.read_text())
    except (json.JSONDecodeError, OSError) as e:
        raise AssertionError(f"'{filepath}' is not valid JSON: {e}")


@then('"{filepath}" has integer key "{key}"')
def step_json_has_int_key(context, filepath, key):
    data = json.loads((context.ws / filepath).read_text())
    assert key in data, f"Key '{key}' not found in '{filepath}'. Keys: {list(data)}"
    assert isinstance(data[key], int), (
        f"Key '{key}' in '{filepath}' is {type(data[key]).__name__}, expected int"
    )


@then('"{filepath}" key "{key}" is greater than {value:d}')
def step_json_key_gt(context, filepath, key, value):
    data = json.loads((context.ws / filepath).read_text())
    actual = data.get(key)
    assert isinstance(actual, int) and actual > value, (
        f"'{filepath}'.{key} = {actual}, expected > {value}"
    )
