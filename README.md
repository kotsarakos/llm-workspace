# llm-workspace

**A private, self-hosted workspace for running and chatting with your own LLMs, with a redesigned animated interface.**

llm-workspace is a customized build of [Open WebUI](https://github.com/open-webui/open-webui). It runs fully on your own machine, connects to local models through [Ollama](https://ollama.com), and keeps chats, documents and settings on your hardware. On top of the upstream platform it adds a redesigned UI, a reworked settings experience and a leaner codebase.

> Built on Open WebUI. The Open WebUI name and logo are kept as its license requires; see [License & credits](#license--credits).

<!--
Screenshots: add images to docs/screenshots/ and uncomment.
![Sign-in page](docs/screenshots/sign-in.png)
![Chat](docs/screenshots/chat.png)
![Settings](docs/screenshots/settings.png)
-->

---

## Highlights

### Redesigned interface
A consistent blue, violet and cyan theme built from animated [Svelte Bits](https://github.com/DavidHDev/svelte-bits) components (WebGL and CSS, no extra runtime dependencies):

| Area | What changed |
|---|---|
| Sign-in | Aurora WebGL background, "decrypting" animated title, star-border sign-in button |
| App shell | Animated DarkVeil backdrop and click-spark interaction feedback |
| Sidebar | Frosted-glass panel with a shining "New Chat" action |
| Composer | Cursor-reactive glowing border around the message box |
| New chat | Animated gradient greeting |

Every effect follows light/dark mode, pauses when off-screen or in a hidden tab, and respects the OS "reduce motion" setting.

### Settings, rebuilt for readability
- Larger type scale (default 10–12px raised to 13–15px)
- Sections rendered as glass cards with gradient headings, dividers and hover states
- Accent-styled tabs, switches, dropdowns, inputs and save buttons
- Implemented through the shared section/row/field components, so every user and admin settings page gets the same design from one scoped stylesheet

### Leaner codebase
- Removed 65 frontend files unreachable from any route, found with a custom import-graph analysis and verified before deletion
- Dropped 15 unused npm packages (~184 including transitive dependencies)
- Removed upstream release and publishing pipelines that don't apply to this project

### Local-first by default
- Runs in Docker, bound to `localhost` only
- Uses your existing Ollama models; no data leaves your machine
- One-command build and run script

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | SvelteKit, Svelte 5, TypeScript, Tailwind CSS v4 |
| UI effects | Svelte Bits (WebGL2 shaders, canvas, CSS) |
| Backend | Python, FastAPI |
| Models | Ollama (local LLMs) and OpenAI-compatible APIs |
| Deployment | Docker |

```
Browser ──► llm-workspace (Docker, localhost:3000)
              ├─ SvelteKit frontend
              └─ FastAPI backend ──► Ollama (host, :11434) ──► local models
```

---

## Quick start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Ollama](https://ollama.com) running on the host, with at least one model:
  ```bash
  ollama pull qwen3:4b
  ```

### Run
```bash
git clone https://github.com/kotsarakos/llm-workspace.git
cd llm-workspace
./docker-run.sh
```

Open **http://localhost:3000**. The first account you create becomes the administrator.

| Variable | Default | Purpose |
|---|---|---|
| `LLM_WORKSPACE_PORT` | `3000` | Port on localhost |
| `OLLAMA_BASE_URL` | `http://host.docker.internal:11434` | Where Ollama is reachable from the container |

Data (users, chats, settings) is stored in the Docker volume `llm-workspace-data` and survives rebuilds.

### Model tips
Tools such as web search and memory are enabled by default and need a model that supports tool calling, for example `qwen3`, `llama3.1` or `llama3.2`. For models without tool support (e.g. `gemma3`), set **Admin Settings → Models → *model* → Advanced Params → Function Calling** to **Legacy**.

---

## Development

```bash
npm install
npm run dev        # frontend dev server with hot reload at http://localhost:5173
```

Custom work lives mainly in:

| Path | Contents |
|---|---|
| `src/lib/components/svelte-bits/` | Animated UI components and the shared theme (`theme.ts`) |
| `src/app.css` (end of file) | Scoped settings-window design (`.llmw-settings`) |
| `src/routes/auth/+page.svelte` | Sign-in page |
| `src/routes/(app)/+layout.svelte` | App shell backdrop and effects |
| `docker-run.sh` | Build-and-run script |

---

## Roadmap
- [ ] Screenshots and a short demo GIF
- [ ] Docker Compose setup with optional GPU support
- [ ] Optional cloud deployment with HTTPS and authentication
- [ ] Custom model presets for specific business workflows

---

## License & credits

- **Open WebUI**: this project is built on [Open WebUI](https://github.com/open-webui/open-webui), created by [Timothy Jaeryang Baek](https://github.com/tjbck) and maintained by Open WebUI Inc. and its contributors. It includes code under the Open WebUI License, which requires preserving the Open WebUI branding, and prior contributions under their original licenses. See [LICENSE](./LICENSE), [LICENSE_NOTICE](./LICENSE_NOTICE) and [LICENSE_HISTORY](./LICENSE_HISTORY).
- **Svelte Bits**: animated components by [David Haz](https://github.com/DavidHDev/svelte-bits), used under the MIT + Commons Clause license. See [`src/lib/components/svelte-bits/LICENSE.md`](./src/lib/components/svelte-bits/LICENSE.md).
