"""浏览器安全代理契约：前端只能通过普通 JWT 调用课程、活动和会话能力。"""

from main import app


def test_client_proxy_exposes_ten_authenticated_operations():
    schema = app.openapi()
    paths = {path: methods for path, methods in schema["paths"].items() if path.startswith("/api/v1/client/")}
    assert sum(len(methods) for methods in paths.values()) == 10
    assert "/api/v1/client/courses" in paths
    assert "/api/v1/client/events/{event_id}/register" in paths
    assert "/api/v1/client/chat/sessions/{session_id}/messages" in paths

    for methods in paths.values():
        for operation in methods.values():
            assert operation.get("security"), "client proxy operation must require bearer authentication"
