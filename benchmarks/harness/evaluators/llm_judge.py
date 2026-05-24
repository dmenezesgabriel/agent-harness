"""LLM-as-judge for pairwise and pointwise evaluation.

Uses a DIFFERENT model than the agent under test to avoid self-enhancement bias.
Default judge: claude-haiku-4-5 (fast, cheap, different capability profile).

Pairwise mode: given output_a (with_skill) and output_b (without_skill),
ask which better satisfies the task rubric. Position is randomized per call.

Pointwise mode: score a single output on a rubric (0-10).
"""
from __future__ import annotations

import random

import anthropic

from harness.models import TaskResult

_JUDGE_MODEL = "claude-haiku-4-5-20251001"

_PAIRWISE_PROMPT = """You are an objective evaluator assessing software engineering assistant outputs.

## Task
{task_title}

## Instruction given to the assistant
{instruction}

## Output {label_a}
{output_a}

## Output {label_b}
{output_b}

## Evaluation criteria
{rubric}

Which output better satisfies the task instruction and evaluation criteria?
Reply with ONLY one of: "A", "B", or "TIE"
Then on the next line, give a one-sentence reason.
"""

_POINTWISE_PROMPT = """You are an objective evaluator assessing a software engineering assistant output.

## Task
{task_title}

## Instruction given to the assistant
{instruction}

## Output to evaluate
{output}

## Evaluation criteria (rubric)
{rubric}

Score this output on a scale of 0 to 10, where:
- 0-3: Fails to address the task or missing critical elements
- 4-6: Partially addresses the task with notable gaps
- 7-9: Good quality with minor issues
- 10: Excellent, fully satisfies all criteria

Reply with ONLY the integer score (0-10) on the first line, then one sentence explaining it.
"""

_DEFAULT_RUBRIC = """
1. Does the output directly address the stated task?
2. Are all required sections or components present?
3. Is the content specific and actionable (not vague or generic)?
4. Does it follow software engineering best practices?
5. Is it appropriately scoped (not over-engineered, not under-specified)?
"""


class LLMJudge:
    def __init__(self, model: str = _JUDGE_MODEL):
        self.model = model
        self._client = anthropic.Anthropic()

    def pointwise(self, result: TaskResult, task_title: str, instruction: str,
                  rubric: str = _DEFAULT_RUBRIC) -> tuple[float, str]:
        """Score a single output. Returns (score_0_to_10, reason)."""
        if not result.raw_output:
            return 0.0, "empty output"

        prompt = _POINTWISE_PROMPT.format(
            task_title=task_title,
            instruction=instruction,
            output=result.raw_output[:6000],
            rubric=rubric,
        )
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            lines = text.splitlines()
            score = float(lines[0].strip())
            reason = lines[1].strip() if len(lines) > 1 else ""
            return min(max(score, 0.0), 10.0), reason
        except Exception as exc:
            return 0.0, f"judge error: {exc}"

    def pairwise(
        self,
        with_skill: TaskResult,
        without_skill: TaskResult,
        task_title: str,
        instruction: str,
        rubric: str = _DEFAULT_RUBRIC,
    ) -> tuple[str, str]:
        """Compare two outputs. Returns (winner: 'with_skill'|'without_skill'|'tie', reason)."""
        # randomize position to detect position bias
        flip = random.random() < 0.5
        if flip:
            a, b = without_skill, with_skill
            label_a, label_b = "A", "B"
        else:
            a, b = with_skill, without_skill
            label_a, label_b = "A", "B"

        prompt = _PAIRWISE_PROMPT.format(
            task_title=task_title,
            instruction=instruction,
            label_a=label_a,
            label_b=label_b,
            output_a=(a.raw_output or "")[:4000],
            output_b=(b.raw_output or "")[:4000],
            rubric=rubric,
        )
        try:
            response = self._client.messages.create(
                model=self.model,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            lines = text.splitlines()
            verdict = lines[0].strip().upper()
            reason = lines[1].strip() if len(lines) > 1 else ""

            if verdict == "TIE":
                return "tie", reason
            winner_is_a = verdict == "A"
            if flip:
                # A=without, B=with
                winner = "without_skill" if winner_is_a else "with_skill"
            else:
                # A=with, B=without
                winner = "with_skill" if winner_is_a else "without_skill"
            return winner, reason
        except Exception as exc:
            return "tie", f"judge error: {exc}"
