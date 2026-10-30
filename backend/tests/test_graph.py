from chatbot.agent import build_graph, run_agent
from chatbot.llm import FakeLLM, LLMMessage


async def test_graph_returns_llm_reply() -> None:
    graph = build_graph(FakeLLM())

    reply = await run_agent(graph, [LLMMessage("system", "be helpful"), LLMMessage("user", "ping")])

    assert reply == "[fake-llm] Thanks for reaching out! You said: ping"
