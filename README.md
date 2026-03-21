# Kog – Context-Aware CLI AI Agent

**Kog** is a powerful, context-aware command-line interface (CLI) application built in Python. It acts as a local AI agent capable of managing long-term sessions, ingesting and remembering specific document bounds, processing semantic search retrieval, and orchestrating complex tasks autonomously.

The project is built on modern Python tooling:
- **Typer** for beautiful, intuitive CLI architecture.
- **LangChain** and **LangGraph** for ReAct agent routing and tool execution.
- **ChromaDB** for powerful embedded vector storage and semantic search.
- **Ollama** (`qwen2.5:3b` by default) for fast, local LLM execution. 

---

## 🛠 Features
1. **Multi-Session Isolation**: Maintain entirely separate workspaces (e.g. `work` vs `personal`). Context loaded in one session does not contaminate the LLM responses in another.
2. **Persistent Memory**: Documents loaded into Kog are chunked, embedded, and stored locally in ChromaDB underneath `~/.kog/`. You can continually add, drop, and query the vector store across restarts.
3. **Agentic Workflows**: Ask it to perform complex, multi-step actions. The AI will autonomously query its context via semantic search, process the chunked data, and execute side-effect tools (like sending emails) without needing constant supervision.
4. **Local Execution**: Uses Ollama completely locally, prioritizing your data privacy.

---

## 🚀 Installation & Setup

### Prerequisites
1. **[uv](https://github.com/astral-sh/uv)**: An extremely fast Python package and environment manager.
2. **[Ollama](https://ollama.com)**: For running local LLMs. You must pull the specified model before jumping in:
   ```bash
   ollama run qwen2.5:3b
   ```

### Quick Start
1. Clone the repository and navigate to the directory:
   ```bash
   cd kog-cli-agent
   ```
2. Sync the environment using `uv`:
   ```bash
   uv sync
   ```
3. Run `kog` commands locally through `uv`:
   ```bash
   uv run kog --help
   ```

*(Optional)* You can install the CLI globally on your system to use it anywhere:
```bash
uv tool install .
kog --help
```

---

## 💻 Usage & Commands

Kog’s CLI is split between Context tooling, Session management, and AI Agentic interactions. 

### 👁 AI & Agent Interactions
- **`kog task "<prompt>"`**: The flagship command. Triggers the ReAct agent to autonomously solve a prompt using its tools (Semantic Search, Mailing, etc.).
  - *Example:* `kog task "Read the grocery lists in my context and email them to me categorized by dairy and meat."`
- **`kog summarize`**: Provides a quick, holistic summary of all active contexts loaded in your current session.
- **`kog ask "<question>"`**: Directly queries the active chunked contexts to answer a localized query.
- **`kog mail --to <email> --mode summarize`**: Automatically rips the current active context into a summary and shoots it to an email address. 
   *(Note: Uses mock sending by default. You can define `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, and `SMTP_PASS` environment variables for real dispatch).*

### 📁 Session Management
Sessions isolate your workspace workflows.
- **`kog new_session <name>`**: Starts a brand new session with zero contexts actively loaded. If you are currently sitting in an unsaved `default` session with contexts, it will politely prompt you to save it first.
- **`kog list_sessions`**: Displays all active and stored sessions alongside their context counts. The current active session gets a `*` flag.
- **`kog load_session <name>`**: Swaps your active workspace.
- **`kog delete_session <name>`**: Purges a session workspace entirely.
- **`kog ps`**: Prints out your currently active session and exactly which contexts are actively contributing to the LLM's memory.

### 🧠 Context Management
Contexts are documents or files that have been parsed and embedded into ChromaDB.
- **`kog open <file_path>`**: Ingests a raw file (Markdown, TXT, etc.), chunks it, embeds it into ChromaDB, and automatically loads it as an active context identifier into your current session.
- **`kog list_context`**: Shows all globally stored context files living in your `~/.kog/` directory.
- **`kog load_context <name>`**: Explicitly adds a previously embedded context into your current active session.
- **`kog unload_context <name>`**: Detaches a context from your current session *without* deleting it from global storage.
- **`kog delete_context <name>`**: Permanently purges a context from ChromaDB and auto-removes it from any sessions utilizing it.

---

## 🏗 Architecture Details
Kog persists state natively in your user home directory: `~/.kog/`.
- `~/.kog/sessions.json`: Contains routing identifiers assigning context pointers to specific workspaces.
- `~/.kog/contexts.json`: Metadata map mapping file sources to context pointer names.
- `~/.kog/chroma/`: The native ChromaDB embedded vector directory. 


