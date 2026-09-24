from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ai_inspection_without_photos_should_fail():
    # 1. Create a fresh task
    gen_res = client.post(
        "/api/v1/inspection-tasks/generate",
        json={"inspection_date": "2026-09-22", "period": "MORNING"},
    )
    assert gen_res.status_code == 200
    task_id = gen_res.json()[0]["id"]

    # 2. Try analyze without photos -> should fail with 400
    res = client.post(f"/api/v1/inspection-tasks/{task_id}/analyze")
    assert res.status_code == 400
    assert "No uploaded photos" in res.json()["detail"]


def test_ai_inspection_end_to_end_with_real_standards():
    # 1. Generate task
    gen_res = client.post(
        "/api/v1/inspection-tasks/generate",
        json={"inspection_date": "2026-09-22", "period": "NOON"},
    )
    assert gen_res.status_code == 200
    task_id = gen_res.json()[0]["id"]

    # 2. Upload real photos (using the uploaded standard photos as live samples)
    with open("uploads/standards/RM301_FRONT.JPG", "rb") as f_front:
        up_front = client.post(
            "/api/v1/photos/upload",
            data={"task_id": task_id, "photo_type": "FRONT"},
            files={"file": ("front_live.jpg", f_front.read(), "image/jpeg")},
        )
        assert up_front.status_code == 200
        assert up_front.json()["quality_passed"] is True

    with open("uploads/standards/RM301_REAR.JPG", "rb") as f_rear:
        up_rear = client.post(
            "/api/v1/photos/upload",
            data={"task_id": task_id, "photo_type": "REAR"},
            files={"file": ("rear_live.jpg", f_rear.read(), "image/jpeg")},
        )
        assert up_rear.status_code == 200
        assert up_rear.json()["quality_passed"] is True

    # 3. Trigger AI Analysis
    analyze_res = client.post(f"/api/v1/inspection-tasks/{task_id}/analyze")
    assert analyze_res.status_code == 200
    results = analyze_res.json()
    assert len(results) >= 7, f"Expected 7 indicator results, got {len(results)}"

    for r in results:
        assert r["task_id"] == task_id
        assert r["ai_status"] in ("NORMAL", "ABNORMAL", "UNCERTAIN")
        assert r["ai_confidence"] is not None
        assert r["ai_reason"] is not None

    # 4. Check Task Status is now WAITING_CONFIRM
    task_res = client.get(f"/api/v1/inspection-tasks/{task_id}")
    assert task_res.status_code == 200
    assert task_res.json()["status"] == "WAITING_CONFIRM"

    # 5. Check results by-task query
    list_res = client.get(f"/api/v1/inspection-results/by-task/{task_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 7
