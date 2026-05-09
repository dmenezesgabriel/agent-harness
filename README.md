# Pi Setup

1. **Idea**: App, Feature or Refactor
2. **Resarch** (Optional): If difficult exploration phases, create a `research.md` to cache tbem
3. **Prototype** (Optional): Hash out ideais in code to get early feedback and provide assets that can be used later in implementation itself
4. **PRD**: Create a markdown file to describe the destination, with user stories and implementation notes
5. **Kanban**: Turn the PRD into individual tickets with blocking relationships
6. **Implementation**: In a loop, run a coding agent to execute all of the tickets on kanban board
7. **Code review**: Create a QA plan for a human to verify the finished work


## Worflow

1. `/explore-codebase` if exits within a **subagent**
2. `/grill-me`
3. `/write-a-prd` (once broken into issues, get rid of it so it does not get outdated)
4. Check if proposes the implementation on `horizontal` or `vertical` slices, `verical` are preferred (db -> useCase -> Service, instead of entire db first)
5. `/to-issue` break prd into tasks
6. `/tdd` for Implementation (used on **ralph** loops)
7. Review
8. `/improve-codebase` if needed

## Highlights

- TDD is a must have
- Design the interfaces and delegate the implementation

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
