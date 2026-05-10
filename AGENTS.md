## Hardware Constraints

- **RAM**: Max 4GB available (7GB total, shared with Intel Iris Xe GPU via UMA)
- **GPU**: Intel Iris Xe (TGL GT2, Vulkan-capable, UMA = no dedicated VRAM)
- **CPU**: 8 cores, icelake
- **Storage**: NVMe SSD

## LLM Configuration

- **Max model size**: ~800MB (avoids OOM alongside VS Code + browser)
- **Context window**: 4096 tokens default (2048 for Gemma 3 to save memory)
- **Batch size**: `--batch-size 256 --ubatch-size 128`
- **GPU offload**: prefer `-ngl 0` (CPU-only) — UMA means GPU uses the same RAM
- **Flash attention**: `--flash-attn on`
- **Quantization**: Always Q4_K_M

## Recommended Models (in priority order)

| Model | Size | RAM usage | Notes |
|-------|------|-----------|-------|
| Gemma 3 1B IT Q4_K_M | 769 MB | ~1.2 GB | Best speed/quality tradeoff |
| Qwen2.5-Coder-1.5B Q4_K_M | 1.04 GB | ~1.6 GB | Better coding, needs ~2GB free |
| Qwen2.5-1.5B-Instruct Q4_K_M | 1.04 GB | ~1.6 GB | Good general-purpose |

## Local Provider

The llama.cpp server runs at `http://localhost:8080/v1` with OpenAI-compatible API.
Provider name in pi: `local-llama`
The server is started via `./llama/scripts/server.sh <model-name>`.

## Memory-Safe Operations

- Kill llama process before each new model: `pkill -f llama`
- Download models with `curl`, NOT with `llama-cli -hf` (which loads model into RAM)
- Check free memory before starting server: `free -m`
- Keep context at 2048 unless model quality requires more

## Coding Workflow

1. `/explore-codebase` if exploring existing code
2. `/grill-me` for requirements refinement
3. `/write-a-prd` for planning
4. `/to-issue` to break into tasks
5. `/tdd` for implementation
6. Review with `/review-pr`
7. `/improve-codebase` after done
