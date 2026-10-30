"""The support agent as a LangGraph graph.

Today it is a single node that asks the LLM for a reply. The structure is here so the roadmap
items can be added as nodes and edges without reshaping the service layer.

TODO(T1.4): tool-calling loop using the tools from T1.1-T1.3.
TODO(T2.4): retrieval node that grounds answers in policy documents.
TODO(T3.1, T3.2): memory node (conversation summary, customer facts).
TODO(T4.2): approval gate for refunds/exchanges using LangGraph `interrupt`
and a Postgres checkpointer.
"""

from collections.abc import Sequence
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from chatbot.llm import LLMMessage, LLMProvider


class AgentState(TypedDict):
    messages: list[LLMMessage]
    reply: str


AgentGraph = CompiledStateGraph


def build_graph(llm: LLMProvider) -> AgentGraph:
    async def respond(state: AgentState) -> dict[str, Any]:
        return {"reply": await llm.generate(state["messages"])}

    builder = StateGraph(AgentState)
    builder.add_node("respond", respond)
    builder.add_edge(START, "respond")
    builder.add_edge("respond", END)
    return builder.compile()


async def run_agent(graph: AgentGraph, messages: Sequence[LLMMessage]) -> str:
    result = await graph.ainvoke({"messages": list(messages), "reply": ""})
    return result["reply"]
