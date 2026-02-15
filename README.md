<div align="center">

# 🧠 Synapsis — AI Cognitive Assistant

**Your personal, fully local AI memory that never forgets.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)

> **Team**: AI MINDS  
> **Constraint**: Fully local, open-source LLM < 4B params — zero proprietary APIs

</div>

---

## 🔍 The Problem

We constantly capture information across **images, text, audio, documents, and web pages**. Over time, this creates a massive personal information space that's nearly impossible to organize or search. Important knowledge is lost — not because it's unavailable, but because it **can't be retrieved when needed**.

## 💡 Our Solution

**Synapsis** is a zero-touch cognitive assistant that **automatically ingests** your personal data across multiple modalities, understands its meaning, and builds a **persistent, structured memory** you can query with natural language.

> 🚀 No uploads. No tagging. No manual work. Just use your computer — Synapsis learns in the background.

---

## 🏗️ Architecture

![System Architecture](diagram1.png)

## ✨ Key Features

| Feature | Description |
|---|---|
| 📂 **Automatic Multimodal Ingestion** | Watches your directories for text, PDFs, images (OCR), audio, and documents — zero manual uploads |
| 🧩 **Semantic Understanding** | Interprets content meaning and purpose regardless of format |
| 🧠 **Persistent Memory** | Structured knowledge graph (vector + graph DB) that survives restarts and grows over time |
| 💬 **Natural Language Q&A** | Ask questions and get grounded answers with full source citations |
| ✅ **Self-Verification** | Reasons about relevance and verifies its own answers before presenting them |
| 🔗 **Proactive Insights** | Automatically surfaces connections, contradictions, and actionable items across your data |
| 🔒 **Fully Air-Gapped** | Zero internet required — everything runs locally on your machine |

---

## 🔄 Data Flow

![Data Flow](diagram2.png)

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| 🤖 **LLM** | ![Ollama](https://img.shields.io/badge/Phi--4--mini--instruct_(3.8B)-000?style=flat-square&logo=ollama) | Local language model for reasoning & generation |
| 📐 **Embeddings** | ![HuggingFace](https://img.shields.io/badge/all--MiniLM--L6--v2-FFD21E?style=flat-square&logo=huggingface&logoColor=black) | Semantic embeddings (384-dim, fully local) |
| 🗄️ **Vector DB** | ![Qdrant](https://img.shields.io/badge/Qdrant-DC382D?style=flat-square&logo=qdrant&logoColor=white) | Vector similarity search (on-disk persistence) |
| 🕸️ **Graph Store** | ![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white) | Entity & relationship graph persistence |
| ⚡ **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | REST API, ingestion pipeline, reasoning engine |
| 🎨 **Frontend** | ![Next.js](https://img.shields.io/badge/Next.js-000?style=flat-square&logo=nextdotjs) ![Tailwind](https://img.shields.io/badge/Tailwind-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white) | Chat UI, 3D knowledge graph, timeline views |
| 📦 **Deployment** | ![Docker](https://img.shields.io/badge/Docker_Compose-2496ED?style=flat-square&logo=docker&logoColor=white) | One-command local deployment |

---

## ✅ Compliance

| Rule | Status |
|---|---|
| No proprietary APIs | ✅ Zero external API calls |
| LLM < 4B parameters | ✅ Phi-4-mini = 3.8B |
| Fully local & air-gapped | ✅ Localhost only (127.0.0.1) |
| Continuous operation | ✅ Background file watcher + persistent store |
| Persistent memory | ✅ Qdrant + SQLite, survives restarts |
| Open-source model | ✅ MIT licensed |

---

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/Lacoste-INSAT/AI_Minds.git
cd AI_Minds

# 2. Start everything with Docker
docker-compose up --build

# 3. Open the UI
# → http://localhost:3000
```

---

## 👥 Team — AI MINDS

| Member | GitHub |
|---|---|
| **Akram Zaabi** | [@AkramZaabi](https://github.com/AkramZaabi) |
| **Makki Aloulou** | [@MakkiAloulou](https://github.com/MakkiAloulou) |
| **Rami Troudi** | [@Rami-Troudi](https://github.com/Rami-Troudi) |
| **Yassine Kolsi** | [@yassinekolsi](https://github.com/yassinekolsi) |
| **Youssef Rekik** | [@youssefrekik1](https://github.com/youssefrekik1) |

---

<div align="center">

*Built with ❤️ during MSB AI Hackathon*

</div>
