import io
from PIL import Image
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def make_test_image(color=(200, 200, 200), size=(640, 480), noise=True) -> bytes:
    img = Image.new("RGB", size, color=color)
    if noise:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        for i in range(0, size[0], 20):
            draw.line([(i, 0), (size[0] - i, size[1])], fill=(i % 255, (i * 2) % 255, 100), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_photo_upload_pass():
    # 1. First generate a task
    res = client.post(
        "/api/v1/inspection-tasks/generate",
        json={"inspection_date": "2026-09-21", "period": "MORNING"},
    )
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) > 0
    task_id = tasks[0]["id"]

    # 2. Upload valid image
    good_img = make_test_image(size=(800, 600), noise=True)
    res = client.post(
        "/api/v1/photos/upload",
        data={"task_id": task_id, "photo_type": "FRONT"},
        files={"file": ("front_test.jpg", good_img, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["task_id"] == task_id
    assert data["photo_type"] == "FRONT"
    assert data["quality_passed"] is True
    assert data["quality_status"] == "PASS"
    assert data["photo_url"].startswith("/uploads/tasks/")

    # 3. Query photos by task
    list_res = client.get(f"/api/v1/photos/by-task/{task_id}")
    assert list_res.status_code == 200
    photos = list_res.json()
    assert len(photos) >= 1
    assert photos[0]["photo_type"] == "FRONT"


def test_photo_upload_too_dark():
    res = client.post(
        "/api/v1/inspection-tasks/generate",
        json={"inspection_date": "2026-09-21", "period": "NOON"},
    )
    task_id = res.json()[0]["id"]

    # Pitch black image
    black_img = make_test_image(color=(5, 5, 5), noise=False)
    res = client.post(
        "/api/v1/photos/upload",
        data={"task_id": task_id, "photo_type": "FRONT"},
        files={"file": ("dark.jpg", black_img, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["quality_passed"] is False
    assert data["quality_status"] == "TOO_DARK"
    assert "光线过暗" in (data["quality_reason"] or "")


def test_photo_upload_blurry():
    res = client.post(
        "/api/v1/inspection-tasks/generate",
        json={"inspection_date": "2026-09-21", "period": "EVENING"},
    )
    task_id = res.json()[0]["id"]

    # Completely flat grey image (zero texture => Laplacian var = 0)
    blurry_img = make_test_image(color=(128, 128, 128), noise=False)
    res = client.post(
        "/api/v1/photos/upload",
        data={"task_id": task_id, "photo_type": "REAR"},
        files={"file": ("blurry.jpg", blurry_img, "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["quality_passed"] is False
    assert data["quality_status"] == "BLURRY"
    assert "模糊" in (data["quality_reason"] or "")
