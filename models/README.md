# Custom Ollama models

Variants of existing models, defined as Ollama Modelfiles. `./start.sh` creates each one automatically when its base model is installed.

| Folder | Model name | Based on | What it adds |
|---|---|---|---|
| [`gemma3-tools/`](gemma3-tools/) | `gemma3-tools` | `gemma3:4b` | Tool calling (stock Gemma 3 is rejected by Ollama with "does not support tools") |

## gemma3-tools
The stock template has no `{{ .Tools }}` section, so Ollama does not offer tool calling for Gemma 3. The custom template:
- lists the available tools in a compact, readable form (name, description, arguments, allowed values) instead of raw JSON Schema, which small models follow better,
- shows the exact call for tools without arguments,
- asks for a single raw-JSON function call and renders earlier calls and tool results back to the model,
- lowers the temperature to 0.4 for more consistent calls.

Ollama detects the tools section, reports the `tools` capability and parses the JSON replies into structured tool calls, so the model works with MCP tools in llm-workspace without any special setting.

**Accuracy** on 7 Spotify prompts (actions in English and Greek, plus a general question): went from **unusable** (Ollama rejects tools) to **5/7**, with every action request handled correctly. The remaining misses are model limits: it sometimes wraps the JSON in a code fence, or declines a general question when tools are present. For dependable tool use prefer a model trained for it, such as `qwen3`.

Build manually:
```bash
ollama create gemma3-tools -f models/gemma3-tools/Modelfile
```
