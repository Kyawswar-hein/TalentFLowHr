# 🚀 TalentFlowHR | HR Talent Intelligence & Resume RAG Platform

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)
![LangChain](https://img.shields.io/badge/LangChain-RAG-0055FF)
![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Workflows-orange)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql)
![Ollama](https://img.shields.io/badge/Ollama-Llama_3.1-black)

**TalentFlowHR** is an AI-powered HR Talent Intelligence and Candidate Matching platform. Built with **FastAPI**, **LangChain**, and **LangGraph**, it leverages Agentic Retrieval-Augmented Generation (RAG) and local vector search via **PostgreSQL (`pgvector`)** to parse, index, and rank candidate profiles—supporting both **English and Japanese language resumes**—against complex job requirements with high precision, privacy, and speed.

---

## ✨ Key Features

* 📄 **Multi-Format Document Parsing**: Ingests candidate resumes in **PDF, DOCX, and TXT** formats, extracting structured entity data and technical skills.
* 🌐 **Bilingual & Japanese Support**: Multi-lingual processing optimized for Japanese (日本語) and English resumes, ensuring accurate tokenization, cross-lingual matching, and semantic search.
* 🧠 **Agentic RAG Pipeline**: Combines semantic vector retrieval with **LangGraph** workflows for multi-step reasoning, candidate qualification checks, and re-ranking.
* 🔍 **Semantic Vector Search (`pgvector`)**: Stores and queries high-dimensional embeddings directly in PostgreSQL using `pgvector` for fast local similarity search.
* 🤖 **100% Local LLM Inference**: Uses **Ollama (`Llama 3.1`)** for cost-effective, private, on-premise AI evaluation without external API dependencies.
* ⚡ **Async REST API**: Built on **FastAPI** with asynchronous endpoint execution and strict Pydantic schema validation.

---

## 🏗️ Retrieval-Augmented Generation (RAG) Workflow

```text
  [ Resume Files ] (PDF, DOCX, TXT | EN / JP)
          │
          ▼
  [ Document Loader & Text Chunker ]
          │
          ▼
  [ Vector Embeddings ] ──► [ PostgreSQL + pgvector ]
                                   │
  [ Job Requirement Query ] ───────┤ (Semantic Similarity Search)
                                   ▼
                       [ Top Candidates Retrieved ]
                                   │
                                   ▼
                        [ LangGraph Agent Node ]
                       (Rerank & Score w/ Llama 3.1)
                                   │
                                   ▼
                       [ Matches & HR Analytics ]
