# 🚀 TalentFlowHR | HR Talent Intelligence & Resume RAG Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-RAG-0055FF)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Workflows-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql)
![Ollama](https://img.shields.io/badge/Ollama-Llama_3.1-black)

**TalentFlowHR** is an AI-powered HR Talent Intelligence and Candidate Matching platform. Built with **FastAPI**, **LangChain**, and **LangGraph**, it leverages Retrieval-Augmented Generation (RAG) and local vector search via **PostgreSQL (`pgvector`)** to parse, index, and rank resume profiles against complex job requirements with high precision and low latency.

---

## ✨ Key Features

* 📄 **Automated Resume Parsing & Embedding**: Ingests candidate resumes (PDF/DOCX/TXT), extracts key structured data, and generates semantic vector embeddings.
* 🔍 **Semantic Vector Search (`pgvector`)**: Stores and queries candidate embeddings locally using `pgvector` inside PostgreSQL for high-speed similarity search.
* 🤖 **Local LLM Orchestration**: Powered by **Ollama (`Llama 3.1`)** for cost-effective, private, on-premise AI inference without external API dependencies.
* 🧠 **Agentic Workflow Control**: Uses **LangGraph** to manage multi-step reasoning, dynamic filtering, candidate qualification checks, and custom evaluation flows.
* ⚡ **High-Performance REST API**: Built on **FastAPI** with asynchronous endpoint execution and strict Pydantic data validation.

---

## 🛠️ Architecture & Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** | Asynchronous Python REST API interface |
| **Orchestration** | **LangChain & LangGraph** | RAG pipelines, prompt management, and stateful agent logic |
| **LLM Engine** | **Ollama (Llama 3.1)** | Local open-source Large Language Model inference |
| **Vector Database** | **PostgreSQL + `pgvector`** | Vector extension for high-performance similarity queries |
| **Environment** | **Python 3.10+** | Virtual environment managed with strict dependency controls |

---

## 📁 Repository Structure

```text
TalentFlowHR/
├── app/
│   ├── api/            # FastAPI route handlers
│   ├── core/           # Configuration and database connection setups
│   ├── graph/          # LangGraph state workflows and agent nodes
│   ├── services/       # RAG services, embedding generation, and vector search
│   └── models/         # Pydantic models & SQLAlchemy DB schemas
├── data/               # Document store / sample resumes (gitignored)
├── .gitignore          # Git exclusion rules
├── requirements.txt    # Project dependencies
└── main.py             # FastAPI entry point
