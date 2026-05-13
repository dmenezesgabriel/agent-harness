# Pi Setup

1. **Idea**: App, Feature, or Refactor
2. **Research** (optional): If the exploration phase is difficult, create a `research.md` to cache findings
3. **Prototype** (optional): Hash out ideas in code to get early feedback and reusable assets for implementation
4. **PRD**: Create a markdown file that describes the destination, with user stories and implementation notes
5. **Kanban**: Turn the PRD into individual tickets with blocking relationships
6. **Implementation**: In a loop, run a coding agent to execute all tickets on the Kanban board
7. **Code review**: Create a QA plan for a human to verify the finished work


## Workflow

1. `/explore-codebase` if it exists within a **subagent**
2. `/grill-me`
3. `/write-a-prd` (once broken into issues, remove it so it does not get outdated)
4. Prefer **vertical** implementation slices (`db -> use case -> service`) over horizontal slices
5. `/to-issue` to break the PRD into tasks
6. `/tdd` for implementation (used on **ralph** loops)
7. Review
8. `/improve-codebase` if needed

## Highlights

- TDD is required
- Design interfaces, then delegate implementation

## Skill authoring

- Keep each skill directory self-contained.
- Make `name` match the folder name.
- Write `description` as a precise trigger: what the skill does and when to use it.
- Keep `SKILL.md` lean; move reusable logic into `scripts/` and supporting detail into `references/`.

## Skill evaluation

- Put per-skill cases in `skills/<skill>/evals/evals.json`.
- Use train cases to tune descriptions and instructions; keep validation cases held out.
- Use `scripts/skill-evals/inventory.py` to rank skills by eval priority.
- Use `scripts/skill-evals/split_queries.py` to stratify trigger prompts.
- Use `scripts/skill-evals/score_triggers.py` for trigger accuracy and near-miss diagnostics.
- Use `scripts/skill-evals/score_outputs.py` for assertion grading on captured outputs.
- Use `scripts/skill-evals/generate_variants.py` to render non-destructive skill variants into `experiments/variants/` for prompt/skill experiments.
- Use `scripts/skill-evals/semantic_score.py` for optional embedding-based routing diagnostics and failure clustering.
- Use `scripts/skill-evals/semantic_split.py` for optional embedding-aware train/validation splits.
- Use `scripts/skill-evals/run_dataviz_mlflow.py` to auto-split the dataviz manifest, score both eval types, and log local MLflow runs (`--tracking-uri file:./mlruns`); inspect them with `uvx mlflow ui --backend-store-uri file:./mlruns`.
- Use `scripts/skill-evals/run_skill_mlflow.py` to score any skill manifest, log trigger/output metrics, and compare generated variants in MLflow.
- Use `scripts/skill-evals/report.py` to aggregate benchmark summaries.
- See `docs/skill-experiments.md` for the end-to-end variant generation + MLflow workflow.

## Installing skills

 ```sh
 npx skills add <owner/repo> --skill <skill-name>
 ```

## LLama.cpp

- **get llama.cpp release**:

```sh
mkdir -p llama && \
curl -L "https://github.com/ggml-org/llama.cpp/releases/download/b9093/llama-b9093-bin-ubuntu-vulkan-x64.tar.gz" \
  | tar -xz -C llama --strip-components=1
```

- **check version**:

```sh
./llama/llama-cli --version
```

- **See if works**:


```sh
./llama/llama-cli \
  -hf ggml-org/gemma-3-1b-it-GGUF \
  -ngl 999 \
  -p "Explain llama.cpp in one paragraph"
```

## References

- https://medium.com/@rosgluk/claude-skills-and-skill-md-for-developers-vs-code-jetbrains-cursor-775d96effe58
- https://github.com/mattpocock/ai-engineer-workshop-2026-project
- https://github.com/vercel-labs/agent-browser
- https://github.com/steipete/mcporter
- https://docs.fallow.tools
- https://github.com/amosblomqvist/pi-config/
- https://github.com/nicobailon
- https://huggingface.co/LiquidAI/LFM2-1.2B-RAG-GGUF
- https://www.youtube.com/watch?v=5LTDuOg9DVo
- https://www.youtube.com/watch?v=wJEP4CuR6a4
- [LLM Studio](https://lmstudio.ai/)
- [OpenWebUI](https://github.com/open-webui/open-webui)
- [Skills](https://www.skills.sh/)
- [Skills Spec](https://agentskills.io/specification)
- https://www.youtube.com/watch?v=rcRS8-7OgBo
- https://arxiv.org/html/2311.11482v7


## Pi used extensions

- [pi-mcp-adapter](https://github.com/nicobailon/pi-mcp-adapter)
- [pi-subagents](https://github.com/nicobailon/pi-subagents)
- [pi-web-access](https://github.com/nicobailon/pi-web-access)