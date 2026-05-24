from harness.adapters.claude_code import ClaudeCodeAdapter
from harness.adapters.opencode import OpenCodeAdapter
from harness.adapters.pi_agent import PiAgentAdapter
from harness.registry import adapter_registry

adapter_registry.register("claude-code", ClaudeCodeAdapter)
adapter_registry.register("pi-agent", PiAgentAdapter)
adapter_registry.register("opencode", OpenCodeAdapter)
