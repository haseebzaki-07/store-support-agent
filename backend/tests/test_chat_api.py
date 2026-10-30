from httpx import AsyncClient


async def test_new_conversation_returns_reply_and_session(client: AsyncClient) -> None:
    response = await client.post("/api/chat/message", json={"message": "Where is my order?"})

    assert response.status_code == 200
    body = response.json()
    # The UI contract is camelCase.
    assert set(body) == {"reply", "sessionId", "messageId", "timestamp"}
    assert "Where is my order?" in body["reply"]
    assert body["sessionId"]


async def test_conversation_continues_and_history_is_ordered(client: AsyncClient) -> None:
    first = (await client.post("/api/chat/message", json={"message": "hello"})).json()
    session_id = first["sessionId"]
    second = await client.post(
        "/api/chat/message",
        json={"message": "what is your return policy?", "sessionId": session_id},
    )
    assert second.status_code == 200
    assert second.json()["sessionId"] == session_id

    history = await client.get("/api/chat/message", params={"sessionId": session_id})

    assert history.status_code == 200
    body = history.json()
    assert body["sessionId"] == session_id
    assert {"createdAt", "updatedAt"} <= set(body)
    assert [
        (m["sender"], m["text"] if m["sender"] == "USER" else None) for m in body["messages"]
    ] == [
        ("USER", "hello"),
        ("AI", None),
        ("USER", "what is your return policy?"),
        ("AI", None),
    ]


async def test_unknown_session_on_post_is_404(client: AsyncClient) -> None:
    response = await client.post(
        "/api/chat/message", json={"message": "hi", "sessionId": "does-not-exist"}
    )
    assert response.status_code == 404
    assert response.json() == {"error": "Session not found"}


async def test_unknown_session_on_get_is_404(client: AsyncClient) -> None:
    response = await client.get("/api/chat/message", params={"sessionId": "does-not-exist"})
    assert response.status_code == 404
    assert response.json() == {"error": "Session not found"}


async def test_get_without_session_id_is_400(client: AsyncClient) -> None:
    response = await client.get("/api/chat/message")
    assert response.status_code == 400
    assert response.json() == {"error": "sessionId is required"}


async def test_empty_message_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/chat/message", json={"message": ""})
    assert response.status_code == 400
    body = response.json()
    assert body["error"] == "Invalid request"
    assert body["details"][0]["path"] == ["message"]


async def test_message_over_2000_chars_is_rejected(client: AsyncClient) -> None:
    response = await client.post("/api/chat/message", json={"message": "x" * 2001})
    assert response.status_code == 400
    assert response.json()["error"] == "Invalid request"
