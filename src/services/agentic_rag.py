from typing import TypedDict, List, Dict, Any
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.rag import RAGService


class AgentState(TypedDict):
    query: str
    intent: str
    vector_results: List[Dict[str, Any]]
    final_response: str


# Initialize Ollama LLM
llm = ChatOllama(model="llama3.1:latest", temperature=0.1)


async def classify_intent_node(state: AgentState) -> Dict[str, Any]:
    """Classifies recruiter intent using llama3.1."""
    prompt = f"""You are an expert HR Talent AI router.
    Classify the query into one of these intents:
    - 'vector_search': User wants to find candidates, search skills, or review experience.
    - 'interview_prep': User asks to generate interview questions, screen a candidate, or evaluate job fit.

    Query: {state['query']}
    Return ONLY one word ('vector_search' or 'interview_prep')."""

    response = await llm.ainvoke([HumanMessage(content=prompt)])
    intent = response.content.strip().lower()

    if "interview" in intent:
        return {"intent": "interview_prep"}
    return {"intent": "vector_search"}


async def synthesize_response_node(state: AgentState) -> Dict[str, Any]:
    """Synthesizes candidate vector records into a coherent HR response."""
    chunks = state.get("vector_results", [])

    if not chunks:
        return {"final_response": "No matching candidate records found in the database."}

    context_str = "\n\n".join([
        f"Document: {c.get('document_name', 'Resume')}\nContent: {c.get('content', '')}"
        for c in chunks
    ])

    system_prompt = """You are TalentFlow AI, an expert recruitment and talent management intelligence agent.
    Provide a concise, direct analysis addressing the recruiter's query based ONLY on the candidate context provided.
    If searching for candidates with zero experience or specific skills, clearly summarize who fits best and why."""

    user_prompt = f"Recruiter Query: {state['query']}\n\nCandidate Resume Context:\n{context_str}"

    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])

    return {"final_response": response.content}


def build_agent_graph(db: AsyncSession):
    """Builds and compiles the state graph workflow."""
    rag_service = RAGService(db)

    async def vector_search_node(state: AgentState) -> Dict[str, Any]:
        results = await rag_service.retrieve_relevant_context(
            search_query=state["query"],
            top_k=4
        )
        return {"vector_results": results}

    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("classify", classify_intent_node)
    workflow.add_node("vector_search", vector_search_node)
    workflow.add_node("synthesize", synthesize_response_node)

    # Graph Control Flow
    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "vector_search")
    workflow.add_edge("vector_search", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()