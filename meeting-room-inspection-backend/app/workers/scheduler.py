from datetime import date, datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.inspection_period_config import InspectionPeriodConfig
from app.models.inspection_task import InspectionTask
from app.models.meeting_room import MeetingRoom
from app.services.notification_service import get_notification_service

scheduler = AsyncIOScheduler()


def generate_and_notify_period(period_code: str):
    """
    Called by cron scheduler to generate tasks for the active period and send DingTalk notifications.
    """
    db = SessionLocal()
    try:
        today = date.today()
        period_cfg = db.scalar(
            select(InspectionPeriodConfig).where(
                InspectionPeriodConfig.period_code == period_code
            )
        )
        period_name = period_cfg.period_name if period_cfg else period_code

        # 1. Fetch active inspection rooms
        rooms = db.scalars(
            select(MeetingRoom).where(
                MeetingRoom.status == "ACTIVE",
                MeetingRoom.inspection_enabled.is_(True),
            )
        ).all()

        tasks_info = []

        for room in rooms:
            # Idempotently find or create
            task = db.scalar(
                select(InspectionTask).where(
                    InspectionTask.room_id == room.id,
                    InspectionTask.inspection_date == today,
                    InspectionTask.period == period_code,
                )
            )
            if not task:
                task_no = f"IR-{today.strftime('%Y%m%d')}-{room.id}-{period_code}"
                task = InspectionTask(
                    task_no=task_no,
                    room_id=room.id,
                    inspection_date=today,
                    period=period_code,
                    status="PENDING",
                )
                db.add(task)
                db.commit()
                db.refresh(task)

            tasks_info.append({
                "task_id": task.id,
                "room_name": room.room_name,
                "task_no": task.task_no,
            })

        # 2. Push Notification
        notifier = get_notification_service()
        notifier.notify_new_inspection_tasks(
            tasks_info=tasks_info,
            period_name=period_name,
            inspection_date=str(today),
        )

        print(f"[{datetime.now()}] Generated {len(tasks_info)} tasks for {period_name} and dispatched notifications.")

    except Exception as e:
        print(f"Error in scheduler job for period {period_code}: {e}")
    finally:
        db.close()


def setup_scheduler():
    if not settings.scheduler_enabled:
        print("Scheduler is disabled in configuration.")
        return

    db = SessionLocal()
    try:
        periods = db.scalars(
            select(InspectionPeriodConfig).where(InspectionPeriodConfig.enabled.is_(True))
        ).all()

        for p in periods:
            hour = p.start_time.hour
            minute = p.start_time.minute
            job_id = f"job_inspection_{p.period_code.lower()}"

            # Add daily cron job
            scheduler.add_job(
                generate_and_notify_period,
                trigger="cron",
                hour=hour,
                minute=minute,
                args=[p.period_code],
                id=job_id,
                replace_existing=True,
            )
            print(f"✓ Registered inspection cron [{job_id}] at {hour:02d}:{minute:02d} daily for {p.period_name}")

        scheduler.start()
        print("APScheduler started successfully.")
    except Exception as e:
        print(f"Failed to initialize scheduler: {e}")
    finally:
        db.close()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("APScheduler stopped.")
