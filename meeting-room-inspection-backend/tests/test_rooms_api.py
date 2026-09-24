from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_rooms_seeded():
    response = client.get("/api/v1/rooms")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    room = data["items"][0]
    assert room["room_code"] == "RM-301"
    assert room["room_name"] == "301会议室"
    assert room["status"] == "ACTIVE"
    assert room["inspection_enabled"] is True
