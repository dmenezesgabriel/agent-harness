# Harness setup

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