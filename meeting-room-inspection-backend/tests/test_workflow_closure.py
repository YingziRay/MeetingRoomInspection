from fastapi.testclient import TestClient
from app.main import app
from app.services.notification_service import get_notification_service
from app.workers.scheduler import generate_and_notify_period

client = TestClient(app)


def test_batch_confirm_and_submit_workflow():
    # 1. Generate Task
    gen_res = client.post(
        "/api/v1/inspection-tasks/generate",
        json={"inspection_date": "2026-09-23", "period": "MORNING"},
    )
    assert gen_res.status_code == 200
    task_id = gen_res.json()[0]["id"]

    # 2. Upload both FRONT and REAR photos
    with open("uploads/standards/RM301_FRONT.JPG", "rb") as f_front:
        client.post(
            "/api/v1/photos/upload",
            data={"task_id": task_id, "photo_type": "FRONT"},
            files={"file": ("front.jpg", f_front.read(), "image/jpeg")},
        )
    with open("uploads/standards/RM301_REAR.JPG", "rb") as f_rear:
        client.post(
            "/api/v1/photos/upload",
            data={"task_id": task_id, "photo_type": "REAR"},
            files={"file": ("rear.jpg", f_rear.read(), "image/jpeg")},
        )

    # 3. Trigger AI Analysis
    client.post(f"/api/v1/inspection-tasks/{task_id}/analyze")

    # 4. Fetch results
    res_list = client.get(f"/api/v1/inspection-results/by-task/{task_id}").json()
    assert len(res_list) >= 7

    # 5. Batch Confirm: confirm all as AI + modify one specific item
    first_item = res_list[0]
    confirm_payload = {
        "task_id": task_id,
        "confirm_all_as_ai": True,
        "items": [
            {
                "result_id": first_item["id"],
                "human_status": "NORMAL",
                "human_remark": "巡检员现场核实确认合格",
            }
        ],
    }
    confirm_res = client.post(
        "/api/v1/inspection-results/batch-confirm",
        json=confirm_payload,
    )
    assert confirm_res.status_code == 200
    updated_items = confirm_res.json()
    assert len(updated_items) >= 7
    # Check that first item is explicitly updated
    target = next(i for i in updated_items if i["id"] == first_item["id"])
    assert target["human_status"] == "NORMAL"
    assert target["human_remark"] == "巡检员现场核实确认合格"

    # 6. Submit Task
    submit_res = client.post(
        f"/api/v1/inspection-tasks/{task_id}/submit",
        json={"confirm_all": True, "force_confirm_uncertain": True, "inspector_id": "inspector_zhang"},
    )
    assert submit_res.status_code == 200
    submit_data = submit_res.json()
    assert submit_data["status"] == "COMPLETED"
    assert submit_data["normal"] >= 1
    assert submit_data["uncertain"] == 0

    # Verify task state in database
    task_res = client.get(f"/api/v1/inspection-tasks/{task_id}").json()
    assert task_res["status"] == "COMPLETED"
    assert task_res["inspector_id"] == "inspector_zhang"


def test_notification_service():
    notifier = get_notification_service()
    success = notifier.notify_new_inspection_tasks(
        tasks_info=[{"task_id": 999, "room_name": "301会议室", "task_no": "IR-20260923-1-MORNING"}],
        period_name="上午巡检",
        inspection_date="2026-09-23",
    )
    assert success is True


def test_scheduler_task_generation():
    # Calling the job directly
    generate_and_notify_period("MORNING")
