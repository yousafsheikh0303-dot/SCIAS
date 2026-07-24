import os
import sqlite3
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from groq import RateLimitError
from dotenv import load_dotenv

from agents.disease_agent import disease_agent
from agents.market_agent import market_agent
from agents.weather_agent import weather_agent
from agents.irrigation_agent import irrigation_agent
from agents.rag_agents import rag_query
from agents.yield_agent import yield_agent
from agents.translation_agent import detect_and_translate_to_english, translate_from_english

load_dotenv()

# Absolute path to the DB, anchored to this file's location, so it resolves
# correctly no matter what directory the app is launched from.
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "scias.db")


class SCIASState(TypedDict):
    query: str              # original, possibly non-English, farmer input
    english_query: str      # translated-to-English version used internally
    detected_language: str  # ISO code detected from the original query
    session_id: str
    route: str
    answer: str              # English answer from the agent
    final_answer: str        # answer translated back to farmer's language
    agent_used: str
    image_path: Optional[str]


router_llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


def translate_entry(state: SCIASState) -> SCIASState:
    """Entry point: detect language, translate the farmer's query to English."""
    result = detect_and_translate_to_english(state["query"])
    state["detected_language"] = result["detected_language"]
    state["english_query"] = result["english_text"]
    return state


def route_query(state: SCIASState) -> SCIASState:
    """Classifies the farmer's (now-English) query into one of 6 agent categories."""
    query = state["english_query"]
    image_path = state.get("image_path")

    # A photo was uploaded -> unambiguously a disease query.
    if image_path:
        state["route"] = "disease"
        print(f"[orchestrator] route=disease (image provided) | query='{query}'")
        return state

    routing_prompt = f"""Classify this farmer's query into EXACTLY ONE category. Reply with only the category word, nothing else.

Categories:
- weather (rain, temperature, spraying conditions, frost)
- irrigation (watering schedule, soil moisture, water needs)
- disease (leaf problems, pests, plant symptoms, described in text)
- market (mandi prices, selling, best time/place to sell)
- yield (expected harvest amount, production estimate)
- knowledge (general farming questions, best practices, anything else)

Query: {query}

Category:"""

    try:
        result = router_llm.invoke(routing_prompt)
        category = result.content.strip().lower()
    except RateLimitError:
        category = "knowledge"

    valid_categories = ["weather", "irrigation", "disease", "market", "yield", "knowledge"]
    if category not in valid_categories:
        print(f"[orchestrator] LLM returned invalid category '{category}' -> defaulting to knowledge | query='{query}'")
        category = "knowledge"

    state["route"] = category
    print(f"[orchestrator] route={category} | query='{query}'")
    return state


def call_agent(state: SCIASState) -> SCIASState:
    route = state["route"]
    query = state["english_query"]
    image_path = state.get("image_path")

    agent_map = {
        "weather": weather_agent,
        "irrigation": irrigation_agent,
        "yield": yield_agent,
        "market": market_agent,
    }

    if route == "knowledge":
        result = rag_query(query)
        state["answer"] = result["answer"]
        state["agent_used"] = "knowledge_rag"

    elif route == "disease":
        result = disease_agent(query, image_path=image_path)
        state["answer"] = result["answer"]
        state["agent_used"] = result["agent"]

    else:
        result = agent_map[route](query)
        state["answer"] = result["answer"]
        state["agent_used"] = result["agent"]

    return state


def translate_exit(state: SCIASState) -> SCIASState:
    """Exit point: translate the English answer back to the farmer's original language."""
    target_lang = state.get("detected_language", "en")
    state["final_answer"] = translate_from_english(state["answer"], target_lang)
    return state


def save_to_history(state: SCIASState) -> SCIASState:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (session_id, role, message, agent_used) VALUES (?, ?, ?, ?)",
        (state["session_id"], "user", state["query"], state["agent_used"])
    )
    cursor.execute(
        "INSERT INTO chat_history (session_id, role, message, agent_used) VALUES (?, ?, ?, ?)",
        (state["session_id"], "assistant", state["final_answer"], state["agent_used"])
    )
    conn.commit()
    conn.close()
    return state


# Build the graph: translate in -> route -> agent -> translate out -> save
workflow = StateGraph(SCIASState)
workflow.add_node("translate_entry", translate_entry)
workflow.add_node("router", route_query)
workflow.add_node("agent", call_agent)
workflow.add_node("translate_exit", translate_exit)
workflow.add_node("save_history", save_to_history)

workflow.set_entry_point("translate_entry")
workflow.add_edge("translate_entry", "router")
workflow.add_edge("router", "agent")
workflow.add_edge("agent", "translate_exit")
workflow.add_edge("translate_exit", "save_history")
workflow.add_edge("save_history", END)

scias_graph = workflow.compile()


def run_query(query: str, session_id: str = "default_session", image_path: str = None) -> dict:
    result = scias_graph.invoke({
        "query": query,
        "english_query": "",
        "detected_language": "en",
        "session_id": session_id,
        "route": "",
        "answer": "",
        "final_answer": "",
        "agent_used": "",
        "image_path": image_path,
    })
    return {
        "answer": result["final_answer"],       # native language
        "answer_english": result["answer"],      # English version
        "agent_used": result["agent_used"],
        "detected_language": result["detected_language"],
    }