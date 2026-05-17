# Harness setup

## Installing skills

From an external repository:

```sh
npx skills add <owner/repo> --skill <skill-name>
```

### Installing this repo's own skills into Claude Code

The skills in `skills/` are not picked up by Claude Code automatically — the `skills` CLI must register them explicitly. This is because Claude Code uses its own discovery path (`.agents/skills/` or `.claude/skills/`) rather than the project root `skills/` directory.

Run the helper script to register all skills in this repo for Claude Code (and other supported agents):

```sh
./scripts/install-skills.sh
```

This is equivalent to:

```sh
npx skills add . --skill '*' -y
```

Re-run after adding or renaming skills.

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

### **Articles and Model Repositories**
- [Claude Skills and skill.md for Developers: VS Code, JetBrains, Cursor](https://medium.com/@rosgluk/claude-skills-and-skill-md-for-developers-vs-code-jetbrains-cursor-775d96effe58) — A guide on implementing `skill.md` for AI-assisted development.
- [LiquidAI LFM2 1.2B RAG GGUF](https://huggingface.co/LiquidAI/LFM2-1.2B-RAG-GGUF) — A compact, RAG-optimized Large Foundation Model from Liquid AI.
- [Fallow Tools Documentation](https://docs.fallow.tools) — Documentation for Fallow, a toolset likely focused on developer productivity or data management.

### **GitHub Projects**
- [mattpocock/ai-engineer-workshop-2026-project](https://github.com/mattpocock/ai-engineer-workshop-2026-project) — Project repository for Matt Pocock's 2026 AI Engineer Workshop.
- [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) — A Vercel Labs project for running browser-based AI agents.
- [steipete/mcporter](https://github.com/steipete/mcporter) — A utility by Peter Steinberger for converting and managing Model Context Protocol (MCP) data.
- [amosblomqvist/pi-config](https://github.com/amosblomqvist/pi-config/) — Configuration files and scripts for Raspberry Pi setups.
- [nicobailon (Nico Bailon)](https://github.com/nicobailon) — GitHub profile for developer Nico Bailon.
- [Open WebUI](https://github.com/open-webui/open-webui) — A user-friendly self-hosted WebUI for LLMs (formerly Ollama WebUI).

### **Platforms and Specifications**
- [LM Studio](https://lmstudio.ai/) — A desktop application for discovering and running local LLMs.
- [Skills.sh](https://www.skills.sh/) — A platform for sharing and discovering AI agent capabilities.
- [Agent Skills Specification](https://agentskills.io/specification) — The official technical specification for the "Skills" standard for AI agents.

### **Video Content**
- [The Rise of the AI Engineer (2025)](https://www.youtube.com/watch?v=5LTDuOg9DVo)
- [How to Build Your Own AI Agent with Browser Use](https://www.youtube.com/watch?v=wJEP4CuR6a4)
- [Claude's New "Skills" Feature: A Technical Deep Dive](https://www.youtube.com/watch?v=rcRS8-7OgBo)

### **Scientific Research Papers (arXiv)**
- [Meta Prompting for AI Systems](https://arxiv.org/abs/2311.11482) (Zhang et al., 2023/2025) — A framework for elevating LLM reasoning using modular, task-agnostic prompts.
- [A Practical Guide for Evaluating LLMs and LLM-Reliant Systems](https://arxiv.org/abs/2506.13023) (Rudd et al., 2025) — Guidelines for real-world evaluation of generative AI.
- [Benchmark^2: Systematic Evaluation of LLM Benchmarks](https://arxiv.org/abs/2601.03986) (Qian et al., 2026) — A framework for assessing the quality and consistency of existing LLM benchmarks.
- [FinAuditing: A Financial Taxonomy-Structured Multi-Document Benchmark for Evaluating LLMs](https://arxiv.org/abs/2412.05579) (Wang et al., 2025) — Evaluating model performance on complex, structured financial auditing tasks.
- [Unveiling LLM Evaluation Focused on Metrics: Challenges and Solutions](https://arxiv.org/abs/2404.09135) (Hu & Zhou, 2024) — A comprehensive guide to the mathematical formulations and interpretations of LLM evaluation metrics.

## Pi used extensions

- [pi-mcp-adapter](https://github.com/nicobailon/pi-mcp-adapter)
- [pi-subagents](https://github.com/nicobailon/pi-subagents)
- [pi-web-access](https://github.com/nicobailon/pi-web-access)