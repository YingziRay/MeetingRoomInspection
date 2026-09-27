import csv
import io
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.inspection_indicator import InspectionIndicator
from app.models.inspection_photo import InspectionPhoto
from app.models.inspection_result import InspectionResult
from app.models.inspection_task import InspectionTask
from app.models.meeting_room import MeetingRoom
from app.schemas.dashboard import (
    AbnormalItemSummary,
    DailyTrendItem,
    DashboardStatsResponse,
    IndicatorStatItem,
    RoomStatItem,
    TaskSummaryItem,
)

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """
    获取会议室巡检综合运营统计大盘指标数据
    """
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=14)

    # 1. 查询时间范围内的所有任务
    stmt = select(InspectionTask).where(
        InspectionTask.inspection_date >= start_date,
        InspectionTask.inspection_date <= end_date,
    )
    tasks = db.scalars(stmt).all()
    task_ids = [t.id for t in tasks]

    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == "COMPLETED"]
    completed_count = len(completed_tasks)
    completion_rate = (
        round(completed_count / total_tasks * 100, 1) if total_tasks > 0 else 0.0
    )

    # 2. 查询所有关联指标结果
    results: list[InspectionResult] = []
    if task_ids:
        results = db.scalars(
            select(InspectionResult).where(InspectionResult.task_id.in_(task_ids))
        ).all()

    # 聚合每个任务的异常情况
    task_results_map: dict[int, list[InspectionResult]] = {}
    for r in results:
        task_results_map.setdefault(r.task_id, []).append(r)

    abnormal_task_ids = set()
    total_abnormal_items = 0
    indicator_abnormal_count: dict[int, int] = {}

    for t in completed_tasks:
        t_results = task_results_map.get(t.id, [])
        has_abn = False
        for res in t_results:
            if res.final_status == "ABNORMAL":
                has_abn = True
                total_abnormal_items += 1
                indicator_abnormal_count[res.indicator_id] = (
                    indicator_abnormal_count.get(res.indicator_id, 0) + 1
                )
        if has_abn:
            abnormal_task_ids.add(t.id)

    abnormal_tasks_count = len(abnormal_task_ids)
    normal_tasks_count = completed_count - abnormal_tasks_count
    normal_rate = (
        round(normal_tasks_count / completed_count * 100, 1)
        if completed_count > 0
        else 100.0
    )

    # 3. 统计高频异常指标排行 Top Indicators
    all_indicators = {ind.id: ind for ind in db.scalars(select(InspectionIndicator)).all()}
    top_indicators: list[IndicatorStatItem] = []
    for ind_id, count in sorted(
        indicator_abnormal_count.items(), key=lambda x: x[1], reverse=True
    ):
        ind = all_indicators.get(ind_id)
        if ind:
            percent = (
                round(count / total_abnormal_items * 100, 1)
                if total_abnormal_items > 0
                else 0.0
            )
            top_indicators.append(
                IndicatorStatItem(
                    indicator_id=ind.id,
                    indicator_code=ind.indicator_code,
                    indicator_name=ind.indicator_name,
                    category=ind.category,
                    count=count,
                    percent=percent,
                )
            )

    # 4. 各会议室健康度统计
    rooms = {r.id: r for r in db.scalars(select(MeetingRoom)).all()}
    room_tasks_map: dict[int, list[InspectionTask]] = {}
    for t in tasks:
        room_tasks_map.setdefault(t.room_id, []).append(t)

    room_stats: list[RoomStatItem] = []
    for r_id, r in rooms.items():
        r_tasks = room_tasks_map.get(r_id, [])
        r_completed = [t for t in r_tasks if t.status == "COMPLETED"]
        r_abnormal = [t for t in r_completed if t.id in abnormal_task_ids]
        pass_rate = (
            round((len(r_completed) - len(r_abnormal)) / len(r_completed) * 100, 1)
            if len(r_completed) > 0
            else 100.0
        )
        room_stats.append(
            RoomStatItem(
                room_id=r.id,
                room_name=r.room_name,
                room_code=r.room_code,
                building=r.building,
                floor=r.floor,
                total_tasks=len(r_tasks),
                completed_tasks=len(r_completed),
                abnormal_tasks=len(r_abnormal),
                pass_rate=pass_rate,
            )
        )

    # 5. 每日巡检趋势 Daily Trends (按日期升序)
    daily_map: dict[str, dict[str, int]] = {}
    curr = start_date
    while curr <= end_date:
        d_str = curr.strftime("%Y-%m-%d")
        daily_map[d_str] = {"total": 0, "completed": 0, "abnormal": 0}
        curr += timedelta(days=1)

    for t in tasks:
        d_str = t.inspection_date.strftime("%Y-%m-%d")
        if d_str in daily_map:
            daily_map[d_str]["total"] += 1
            if t.status == "COMPLETED":
                daily_map[d_str]["completed"] += 1
                if t.id in abnormal_task_ids:
                    daily_map[d_str]["abnormal"] += 1

    daily_trends = [
        DailyTrendItem(
            date=d,
            total=v["total"],
            completed=v["completed"],
            abnormal=v["abnormal"],
        )
        for d, v in sorted(daily_map.items())
    ]

    return DashboardStatsResponse(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        total_tasks=total_tasks,
        completed_tasks=completed_count,
        completion_rate=completion_rate,
        normal_tasks=normal_tasks_count,
        abnormal_tasks=abnormal_tasks_count,
        normal_rate=normal_rate,
        total_abnormal_items=total_abnormal_items,
        top_abnormal_indicators=top_indicators,
        room_stats=room_stats,
        daily_trends=daily_trends,
    )


@router.get("/tasks")
def list_inspection_tasks_ledger(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: date | None = None,
    end_date: date | None = None,
    room_id: int | None = None,
    period: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    has_abnormal: bool | None = None,
    db: Session = Depends(get_db),
):
    """
    综合巡检历史台账多维查询（支持时间段、会议室、时段、状态、是否有异常筛选）
    """
    stmt = select(InspectionTask)

    if start_date:
        stmt = stmt.where(InspectionTask.inspection_date >= start_date)
    if end_date:
        stmt = stmt.where(InspectionTask.inspection_date <= end_date)
    if room_id:
        stmt = stmt.where(InspectionTask.room_id == room_id)
    if period:
        stmt = stmt.where(InspectionTask.period == period)
    if status_filter:
        stmt = stmt.where(InspectionTask.status == status_filter)

    # 排序：按巡检日期降序、时段降序、ID降序
    tasks_all = db.scalars(
        stmt.order_by(InspectionTask.inspection_date.desc(), InspectionTask.id.desc())
    ).all()

    # 预加载关联数据 (MeetingRoom, InspectionPhoto, InspectionResult, InspectionIndicator)
    rooms_map = {r.id: r for r in db.scalars(select(MeetingRoom)).all()}
    indicators_map = {i.id: i for i in db.scalars(select(InspectionIndicator)).all()}

    all_task_ids = [t.id for t in tasks_all]
    photos_by_task: dict[int, dict[str, str]] = {}
    if all_task_ids:
        photos = db.scalars(
            select(InspectionPhoto).where(InspectionPhoto.task_id.in_(all_task_ids))
        ).all()
        for p in photos:
            photos_by_task.setdefault(p.task_id, {})[p.photo_type] = p.photo_url

    results_by_task: dict[int, list[InspectionResult]] = {}
    if all_task_ids:
        results = db.scalars(
            select(InspectionResult).where(InspectionResult.task_id.in_(all_task_ids))
        ).all()
        for r in results:
            results_by_task.setdefault(r.task_id, []).append(r)

    # 构建富集台账对象
    enriched_items: list[TaskSummaryItem] = []
    for t in tasks_all:
        room = rooms_map.get(t.room_id)
        room_name = room.room_name if room else f"会议室 #{t.room_id}"
        room_code = room.room_code if room else ""
        building = room.building if room else ""
        floor = room.floor if room else ""

        t_results = results_by_task.get(t.id, [])
        normal_c = sum(1 for r in t_results if r.final_status == "NORMAL")
        abnormal_c = sum(1 for r in t_results if r.final_status == "ABNORMAL")
        uncertain_c = sum(1 for r in t_results if r.final_status == "UNCERTAIN")

        abn_summary: list[AbnormalItemSummary] = []
        for r in t_results:
            if r.final_status == "ABNORMAL":
                ind = indicators_map.get(r.indicator_id)
                abn_summary.append(
                    AbnormalItemSummary(
                        indicator_code=ind.indicator_code if ind else "",
                        indicator_name=ind.indicator_name if ind else f"指标 #{r.indicator_id}",
                        category=ind.category if ind else "",
                        reason=r.human_remark or r.ai_reason or "异常未恢复",
                        status="ABNORMAL",
                    )
                )

        # 过滤是否有异常
        if has_abnormal is True and abnormal_c == 0:
            continue
        if has_abnormal is False and abnormal_c > 0:
            continue

        photos_map = photos_by_task.get(t.id, {})
        enriched_items.append(
            TaskSummaryItem(
                id=t.id,
                task_no=t.task_no,
                room_id=t.room_id,
                room_name=room_name,
                room_code=room_code,
                building=building,
                floor=floor,
                inspection_date=t.inspection_date,
                period=t.period,
                status=t.status,
                inspector_id=t.inspector_id,
                started_at=t.started_at,
                completed_at=t.completed_at,
                total_indicators=len(t_results),
                normal_count=normal_c,
                abnormal_count=abnormal_c,
                uncertain_count=uncertain_c,
                abnormal_summary=abn_summary,
                front_photo_url=photos_map.get("FRONT"),
                rear_photo_url=photos_map.get("REAR"),
            )
        )

    # 分页切片
    total = len(enriched_items)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paged_items = enriched_items[start_idx:end_idx]

    return {
        "items": paged_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/export")
def export_inspection_ledger_csv(
    start_date: date | None = None,
    end_date: date | None = None,
    room_id: int | None = None,
    period: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
):
    """
    导出巡检台账为 Excel 兼容的 CSV 文件（带 UTF-8 BOM，开箱即用不乱码）
    """
    ledger_data = list_inspection_tasks_ledger(
        page=1,
        page_size=10000,
        start_date=start_date,
        end_date=end_date,
        room_id=room_id,
        period=period,
        status_filter=status_filter,
        db=db,
    )

    items: list[TaskSummaryItem] = ledger_data["items"]

    period_names = {
        "MORNING": "上午巡检",
        "NOON": "中午巡检",
        "EVENING": "晚间巡检",
    }
    status_names = {
        "COMPLETED": "已完成",
        "WAITING_CONFIRM": "待人工核验",
        "AI_ANALYZING": "AI分析中",
        "IN_PROGRESS": "巡检中",
        "PENDING": "待巡检",
    }

    output = io.StringIO()
    # 写入 UTF-8 BOM 避免 Excel 中文乱码
    output.write("\ufeff")

    writer = csv.writer(output)
    writer.writerow([
        "任务编号",
        "巡检日期",
        "巡检时段",
        "会议室编号",
        "会议室名称",
        "所属楼层",
        "巡检状态",
        "巡检人员",
        "完成时间",
        "正常项数",
        "异常项数",
        "异常清单及原因详情",
    ])

    for item in items:
        p_name = period_names.get(item.period, item.period)
        s_name = status_names.get(item.status, item.status)
        completed_str = (
            item.completed_at.strftime("%Y-%m-%d %H:%M:%S")
            if item.completed_at
            else "-"
        )
        abn_details = "; ".join([
            f"【{abn.indicator_name}】{abn.reason}"
            for abn in item.abnormal_summary
        ]) if item.abnormal_summary else "全部指标正常"

        writer.writerow([
            item.task_no,
            item.inspection_date.strftime("%Y-%m-%d"),
            p_name,
            item.room_code,
            item.room_name,
            f"{item.building or ''} {item.floor or ''}".strip(),
            s_name,
            item.inspector_id or "-",
            completed_str,
            item.normal_count,
            item.abnormal_count,
            abn_details,
        ])

    csv_data = output.getvalue()
    filename = f"meeting_inspection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
