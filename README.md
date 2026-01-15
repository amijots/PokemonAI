```markdown
# 🔴 Local AI PokéDex Professor

**A completely local, privacy-focused RAG (Retrieval-Augmented Generation) Chatbot that answers questions about Pokémon lore, stats, and moves using Llama 3 and ChromaDB.**

> *Run your own Professor Oak on your PC. No API keys, no subscriptions, no internet required after setup.*

---

## 🚀 Features

*   **100% Local Inference:** Runs on your CPU/GPU using [Ollama](https://ollama.com).
*   **Hybrid Search Engine:** Combines **Semantic Search** (Vector vibes) with **Metadata Filtering** (Math logic like "Speed > 100").
*   **Move Checker Tool:** A specialized Python tool to accurately verify if a Pokémon learns a specific move (e.g., "Can Charizard learn Solar Beam?").
*   **Evolution Logic:** Stitches together complex evolution chains (including items, happiness, and trade requirements).
*   **Agentic Behavior:** Uses LangChain Agents to decide when to look up stats vs. when to check move pools.

---

## 🛠️ Tech Stack

*   **LLM:** Llama 3.1 (8B) via Ollama
*   **Embeddings:** Nomic-Embed-Text via Ollama
*   **Vector DB:** ChromaDB (Local)
*   **Orchestration:** LangChain (Python)
*   **Data Source:** [PokeAPI](https://pokeapi.co)

---

## 📋 Prerequisites

1.  **Python 3.10+**
2.  **[Ollama](https://ollama.com/)** installed and running.
3.  **Hardware:** At least 8GB RAM (16GB recommended) and a decent CPU (or NVIDIA GPU).

---

## 📥 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/local-pokedex-ai.git
cd local-pokedex-ai
```

### 2. Install Dependencies
```bash
pip install requests langchain langchain-community langchain-chroma langchain-ollama lark
```

### 3. Pull Local Models
Open your terminal and pull the necessary models for Ollama:
```bash
# The Chat Brain (Smart enough for tools)
ollama pull llama3.1

# The Embedding Model (Fast & Efficient)
ollama pull nomic-embed-text
```

---

## 🏗️ Usage / Setup

### Step 1: Download Data
Fetch the latest Pokémon data, clean it, and structure it for the AI.
```bash
python download_pokedex.py
```
*Creates `pokedex.json`.*

### Step 2: Clean Move Names (Optional)
Removes hyphens from move names (e.g., `solar-beam` -> `solar beam`) for better matching.
```bash
python clean_moves.py
```

### Step 3: Create the Vector Database
Reads the JSON, generates embeddings, and saves them to the `./pokedex_db` folder.
```bash
python create_db.py
```
*Creates `./pokedex_db` directory.*

### Step 4: Talk to the Professor
Launch the interactive chat loop.
```bash
python chat.py
```

---

## 🧪 Example Queries

The system handles different types of questions using different logic:

| Query Type | What happens under the hood |
| :--- | :--- |
| **"Who is Gengar?"** | **Vector Search:** Looks up the text blob for lore/description. |
| **"Find a Fire type with > 100 Speed"** | **Metadata Filter:** The LLM writes a filter `(type='Fire' AND speed > 100)`. |
| **"Can Squirtle learn Ice Beam?"** | **Tool Call:** The Agent pauses, runs a Python script to check the JSON list, and returns the result. |

---

## 📂 Project Structure

```text
.
├── chat.py                 # Main application (The Agent & UI)
├── create_db.py            # Vector Database generator
├── download_pokedex.py     # Scraper for PokeAPI
├── clean_moves.py          # Utility to format text
├── pokedex.json            # Raw data (The "Reference Library")
└── pokedex_db/             # ChromaDB files (The "Vector Memory")
```

---

## ⚠️ Troubleshooting

**"ImportError: cannot import name 'create_retriever_tool'..."**
*   Your LangChain version is likely outdated or mismatched. Run: `pip install -U langchain langchain-community langchain-core`.

**"The AI says 'I don't know' for color/shape questions."**
*   The `SelfQueryRetriever` in `chat.py` defines fields like `color` and `shape`, but `create_db.py` might not be saving those fields to the database yet. You must update `download_pokedex.py` and `create_db.py` to fetch and store that specific metadata.

**"The AI hallucinates move availability."**
*   Ensure you are using `llama3.1` or `mistral-nemo`. Smaller models like `llama3.2:3b` often struggle to follow Tool Calling instructions strictly.

---

## 📜 License
This project uses data from [PokeAPI](https://pokeapi.co/), which is licensed under BSD-3-Clause.
```