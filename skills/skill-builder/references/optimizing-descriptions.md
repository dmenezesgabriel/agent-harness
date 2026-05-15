# Optimizing Skill Descriptions

Use this reference when writing or refining the `description` field, improving activation precision, debugging false positives, debugging false negatives, or designing trigger evals.

Do not use this file for general skill structure. For strict frontmatter constraints, read `references/specification.md`. For broader instruction quality, read `references/best-practices.md`.

## Core principle

The `description` field is the activation contract.

Agents usually see only each skill’s `name` and `description` during discovery. The full `SKILL.md` is loaded only after the agent decides the skill is relevant.

Therefore, the description must answer:

1. What does this skill do?
2. When should the agent use it?
3. Which task verbs, artifacts, and user intents should trigger it?
4. Which nearby tasks should not trigger it?

## Description pattern

Prefer this shape:

```yaml
description: Use this skill when <user-intent>, including <specific task types>, <artifacts>, and <important nearby terms>.
```

For stricter boundaries:

```yaml
description: Use this skill when <user-intent>. Apply it to <included cases>. Do not use it for <excluded near-misses>.
```

For multi-artifact skills:

```yaml
description: Use this skill when <task>, especially when working with <artifact-1>, <artifact-2>, or <artifact-3>.
```

## Good example

```yaml
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including SKILL.md frontmatter, activation descriptions, instructions, scripts, references, assets, and evals.
```

Why it works:

- Starts with “Use this skill when”.
- Names the user intent.
- Includes relevant task verbs.
- Names concrete artifacts.
- Covers adjacent wording like create, validate, lint, refactor, and fix.
- Avoids unrelated agent, prompt, or software-development tasks.

## Weak examples

Too vague:

```yaml
description: Helps with skills.
```

Too implementation-focused:

```yaml
description: Parses Markdown and YAML files.
```

Too broad:

```yaml
description: Use this skill for prompts, agents, workflows, code, docs, and automation.
```

Too narrow:

```yaml
description: Use this skill only when checking if SKILL.md has a name field.
```

Better:

```yaml
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including SKILL.md frontmatter, activation descriptions, instructions, scripts, references, assets, and evals.
```

## Writing rules

The description should:

- be activation-oriented;
- describe user intent;
- include concrete task verbs;
- include concrete artifacts;
- include important synonyms;
- include near-miss boundaries when needed;
- stay under 1024 characters;
- be specific enough to avoid unrelated triggers;
- be broad enough to catch varied user phrasing.

Prefer:

```text
Use this skill when...
```

Avoid:

```text
This skill helps with...
```

because the agent needs a trigger condition, not a passive summary.

## What to include

Include terms from four categories.

### 1. User intent

What the user is trying to accomplish.

Examples:

```text
create an Agent Skill
validate a skill
fix a broken skill
improve a skill description
add evals to a skill
review skill structure
```

### 2. Task verbs

Actions that should trigger the skill.

Examples:

```text
create
write
generate
validate
lint
fix
repair
refactor
improve
optimize
review
audit
test
evaluate
```

### 3. Artifacts

Concrete files, folders, or concepts.

Examples:

```text
SKILL.md
frontmatter
description
scripts/
references/
assets/
evals/
skill directory
activation
progressive disclosure
support files
```

### 4. Boundaries

Nearby tasks that should not trigger the skill.

Examples:

```text
Do not use for general software architecture unless the task is specifically about packaging it as an Agent Skill.
Do not use for normal Markdown editing unless the file is part of a skill.
Do not use for generic prompt engineering unless the prompt is a skill instruction or activation description.
```

## Good description checklist

Before accepting a description, verify:

- [ ] It starts with or strongly implies “Use this skill when...”
- [ ] It says what the skill does.
- [ ] It says when to use it.
- [ ] It includes likely user verbs.
- [ ] It includes concrete artifacts.
- [ ] It includes domain-specific keywords.
- [ ] It avoids generic claims.
- [ ] It avoids implementation-only wording.
- [ ] It avoids broad unrelated scope.
- [ ] It stays under 1024 characters.
- [ ] It is understandable without reading the skill body.

## Common description fixes

### Vague description

Weak:

```yaml
description: Helps with reports.
```

Better:

```yaml
description: Use this skill when creating, reviewing, or improving executive reports, including structure, key findings, recommendations, evidence, formatting, and final review.
```

### Implementation-focused description

Weak:

```yaml
description: Uses Python scripts to inspect YAML and Markdown.
```

Better:

```yaml
description: Use this skill when validating Agent Skill files, including SKILL.md frontmatter, body sections, support-file references, scripts, assets, and evals.
```

### Too broad

Weak:

```yaml
description: Use this skill for all coding, documentation, and agent tasks.
```

Better:

```yaml
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including SKILL.md, scripts, references, assets, and evals.
```

### Too narrow

Weak:

```yaml
description: Use this skill when the user asks to validate a skill name.
```

Better:

```yaml
description: Use this skill when validating Agent Skills, including directory structure, SKILL.md frontmatter, naming rules, activation descriptions, body instructions, support files, and evals.
```

### Missing artifacts

Weak:

```yaml
description: Use this skill when improving an agent capability.
```

Better:

```yaml
description: Use this skill when improving an Agent Skill, including SKILL.md frontmatter, activation description, workflow instructions, references, scripts, assets, and evals.
```

## Trigger boundaries

Add explicit boundaries when the skill false-triggers on nearby tasks.

Pattern:

```yaml
description: Use this skill when <included task>. Do not use it for <nearby excluded task>.
```

Example:

```yaml
description: Use this skill when creating, validating, or improving Agent Skills. Do not use it for general prompt engineering, documentation editing, or software architecture unless the output is an Agent Skill.
```

Use boundaries sparingly. Too many exclusions can make the description long and harder to match.

## Trigger evals

Use trigger evals to test whether the description activates correctly.

Create realistic prompts labeled with whether the skill should trigger.

Recommended file:

```text
evals/trigger-evals.json
```

Shape:

```json
[
  {
    "id": "create-skill",
    "query": "Create a skill for reviewing frontend accessibility issues.",
    "should_trigger": true
  },
  {
    "id": "fix-skill-description",
    "query": "This SKILL.md description is too broad, can you improve it?",
    "should_trigger": true
  },
  {
    "id": "generic-markdown-edit",
    "query": "Rewrite this README section to be clearer.",
    "should_trigger": false
  }
]
```

Aim for:

- 8-10 should-trigger queries;
- 8-10 should-not-trigger queries;
- realistic phrasing;
- short and long prompts;
- casual and formal prompts;
- typos or imperfect wording;
- near-miss negatives.

## Should-trigger query design

A should-trigger query should represent a task where this skill should help.

Vary:

- wording;
- explicitness;
- detail level;
- artifact names;
- task verbs;
- user context.

Examples:

```json
[
  {
    "query": "Create an Agent Skill for backend API design reviews.",
    "should_trigger": true
  },
  {
    "query": "Can you fix this skill? The description does not trigger correctly.",
    "should_trigger": true
  },
  {
    "query": "Help me add scripts and references to my SKILL.md without bloating context.",
    "should_trigger": true
  },
  {
    "query": "Validate this skill folder and tell me what violates the Agent Skills spec.",
    "should_trigger": true
  }
]
```

## Should-not-trigger query design

A should-not-trigger query should be a near miss, not an obviously unrelated task.

Weak negative:

```json
{
  "query": "What is the weather today?",
  "should_trigger": false
}
```

Better negative:

```json
{
  "query": "Rewrite this Markdown article to be clearer.",
  "should_trigger": false
}
```

Strong negative:

```json
{
  "query": "Improve this prompt for a coding agent, but do not package it as an Agent Skill.",
  "should_trigger": false
}
```

More examples:

```json
[
  {
    "query": "Design a testing strategy for my Python API.",
    "should_trigger": false
  },
  {
    "query": "Refactor this README into better Markdown sections.",
    "should_trigger": false
  },
  {
    "query": "Write a script that validates YAML files.",
    "should_trigger": false
  },
  {
    "query": "Review this architecture prompt for clarity.",
    "should_trigger": false
  }
]
```

## Evaluation loop

Use this loop when optimizing a description:

1. Write 16-20 trigger eval queries.
2. Split them into train and validation sets.
3. Run each query against the agent with the skill installed.
4. Record whether the skill triggered.
5. Identify false negatives in the train set.
6. Identify false positives in the train set.
7. Revise the description using general concepts, not exact overfit phrases.
8. Re-run train.
9. Check validation.
10. Stop when trigger behavior is reliable enough.

Do not optimize only against one prompt.

Do not add every failed query phrase directly into the description.

Generalize from failures.

## Train/validation split

Use train queries to improve the description.

Use validation queries only to check whether the improvement generalizes.

Recommended split:

```text
60% train
40% validation
```

Keep both sets balanced:

- should-trigger examples;
- should-not-trigger examples;
- near-misses;
- varied phrasing.

Do not inspect validation failures repeatedly while rewriting, or the description may overfit.

## Trigger-rate scoring

Because agent behavior can vary, run each query multiple times.

Recommended starting point:

```text
3 runs per query
```

Compute:

```text
trigger_rate = triggered_runs / total_runs
```

Default pass rule:

```text
should_trigger=true  passes when trigger_rate >= 0.50
should_trigger=false passes when trigger_rate < 0.50
```

For stricter settings:

```text
should_trigger=true  passes when trigger_rate >= 0.67
should_trigger=false passes when trigger_rate <= 0.33
```

## Failure analysis

### False negative

The skill should trigger but does not.

Likely causes:

- description is too narrow;
- missing important task verbs;
- missing artifact names;
- user intent is described only in the body;
- description focuses on implementation instead of the user request.

Fix by broadening the description around the general missed intent.

Example false negative:

```text
"Can you add evals to this skill?"
```

Bad fix:

```yaml
description: Use this skill when the user says "add evals to this skill".
```

Better fix:

```yaml
description: Use this skill when creating, validating, improving, or evaluating Agent Skills, including SKILL.md, scripts, references, assets, evals, assertions, and benchmarks.
```

### False positive

The skill triggers but should not.

Likely causes:

- description is too broad;
- generic terms like “agent”, “prompt”, “workflow”, or “documentation” dominate;
- no boundary against nearby tasks;
- scope includes unrelated domains.

Fix by narrowing around the specific artifact or output.

Example false positive:

```text
"Improve this README workflow section."
```

Bad description:

```yaml
description: Use this skill when improving workflows, documentation, instructions, or agents.
```

Better description:

```yaml
description: Use this skill when improving Agent Skills, including SKILL.md instructions, activation descriptions, support files, scripts, assets, and evals.
```

## Revision patterns

### Add missing intent

Before:

```yaml
description: Use this skill when validating SKILL.md files.
```

After:

```yaml
description: Use this skill when creating, validating, linting, refactoring, or fixing Agent Skills, including SKILL.md frontmatter, activation descriptions, instructions, scripts, references, assets, and evals.
```

### Add artifact specificity

Before:

```yaml
description: Use this skill when improving reusable agent workflows.
```

After:

```yaml
description: Use this skill when improving Agent Skills, including SKILL.md, references/, scripts/, assets/, evals/, activation descriptions, and progressive disclosure.
```

### Add boundary

Before:

```yaml
description: Use this skill when improving prompts, instructions, or agent workflows.
```

After:

```yaml
description: Use this skill when improving Agent Skill files and folders. Do not use it for generic prompt engineering unless the prompt is part of SKILL.md or a skill support file.
```

### Reduce over-breadth

Before:

```yaml
description: Use this skill for software design, testing, prompts, docs, agent behavior, and workflows.
```

After:

```yaml
description: Use this skill when packaging software-design, testing, documentation, or workflow expertise into an Agent Skill with SKILL.md, support files, and evals.
```

## Description lint checklist

Review each description manually:

- [ ] Is it activation-oriented?
- [ ] Does it start with “Use this skill when”?
- [ ] Does it name the specific capability?
- [ ] Does it include task verbs?
- [ ] Does it include artifacts?
- [ ] Does it include domain-specific terms?
- [ ] Does it avoid generic “helps with” phrasing?
- [ ] Does it avoid implementation-only phrasing?
- [ ] Does it avoid unrelated broad terms?
- [ ] Does it avoid unnecessary exclusions?
- [ ] Is it under 1024 characters?
- [ ] Would a user prompt with different wording still match?
- [ ] Would a near-miss unrelated prompt avoid matching?

## Optional script interface

If using a trigger-eval script, place it in:

```text
scripts/evaluate_description_triggers.py
```

Expected behavior:

```bash
uv run scripts/evaluate_description_triggers.py \
  --skill-dir . \
  --evals evals/trigger-evals.json \
  --runs 3 \
  --format json
```

The script should report:

```json
{
  "skill_name": "skill-builder",
  "description": "Use this skill when...",
  "summary": {
    "total": 20,
    "passed": 18,
    "failed": 2,
    "pass_rate": 0.9
  },
  "failures": [
    {
      "id": "generic-prompt-edit",
      "query": "Improve this prompt for a coding agent.",
      "should_trigger": false,
      "trigger_rate": 0.67,
      "failure_type": "false_positive"
    }
  ]
}
```

If no trigger-eval script exists, perform the eval manually and record results in:

```text
evals/trigger-results.json
```

## Output format for description reviews

When reviewing a description, return:

```text
Current description:
<description>

Issues:
- <issue>

Improved description:
<new description>

Why this is better:
- <reason>

Trigger coverage:
- Should trigger: <examples>
- Should not trigger: <examples>
```

## Final acceptance checklist

Before finalizing the description:

- [ ] It is valid YAML.
- [ ] It is under 1024 characters.
- [ ] It describes what the skill does.
- [ ] It describes when to use the skill.
- [ ] It includes key task verbs.
- [ ] It includes key artifacts.
- [ ] It avoids broad generic activation.
- [ ] It handles near-miss boundaries when needed.
- [ ] Trigger evals exist for important activation behavior.
- [ ] False positives and false negatives were reviewed.
- [ ] The description does not depend on information only present in the body.
