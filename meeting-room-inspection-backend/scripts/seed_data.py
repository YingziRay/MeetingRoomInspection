import datetime
import sys
from decimal import Decimal
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.db.session import SessionLocal

from app.models.meeting_room import MeetingRoom
from app.models.inspection_indicator import InspectionIndicator
from app.models.inspection_period_config import InspectionPeriodConfig
from app.models.standard_photo import StandardPhoto
from app.models.photo_region import PhotoRegion
from app.models.room_indicator import RoomIndicator


def seed():
    db = SessionLocal()
    try:
        # 1. Inspection Periods
        periods = [
            {
                "period_code": "MORNING",
                "period_name": "上午巡检",
                "start_time": datetime.time(9, 0, 0),
                "deadline_time": datetime.time(10, 30, 0),
                "enabled": True,
                "reminder_enabled": True,
                "reminder_minutes": 15,
                "sort_order": 1,
            },
            {
                "period_code": "NOON",
                "period_name": "中午巡检",
                "start_time": datetime.time(13, 0, 0),
                "deadline_time": datetime.time(14, 30, 0),
                "enabled": True,
                "reminder_enabled": True,
                "reminder_minutes": 15,
                "sort_order": 2,
            },
            {
                "period_code": "EVENING",
                "period_name": "晚间巡检",
                "start_time": datetime.time(18, 0, 0),
                "deadline_time": datetime.time(19, 30, 0),
                "enabled": True,
                "reminder_enabled": True,
                "reminder_minutes": 15,
                "sort_order": 3,
            },
        ]
        for p in periods:
            existing = db.scalar(
                select(InspectionPeriodConfig).where(
                    InspectionPeriodConfig.period_code == p["period_code"]
                )
            )
            if not existing:
                db.add(InspectionPeriodConfig(**p))
        db.commit()
        print("✓ Inspection periods seeded.")

        # 2. Meeting Room 301
        room_301 = db.scalar(
            select(MeetingRoom).where(MeetingRoom.room_code == "RM-301")
        )
        if not room_301:
            room_301 = MeetingRoom(
                room_code="RM-301",
                room_name="301会议室",
                building="总部研发大楼",
                floor="3F",
                location_desc="3楼东侧多功能会议室",
                status="ACTIVE",
                inspection_enabled=True,
            )
            db.add(room_301)
            db.commit()
            db.refresh(room_301)
        print(f"✓ Meeting room 301 ready (id={room_301.id}).")

        # 3. 7 Core Indicators
        indicator_data = [
            {
                "indicator_code": "I001",
                "indicator_name": "灯",
                "category": "DEVICE",
                "description": "检查会议室所有照明灯具是否关闭",
                "normal_condition": "所有照明灯光处于熄灭关闭状态",
                "abnormal_condition": "存在未关闭的照明灯具，灯具处于亮起发光状态",
                "ai_supported": True,
                "enabled": True,
                "sort_order": 1,
            },
            {
                "indicator_code": "I002",
                "indicator_name": "空调",
                "category": "DEVICE",
                "description": "检查空调设备是否已完全关闭",
                "normal_condition": "空调面板指示灯熄灭，出风口摆叶闭合，无送风或运行噪音",
                "abnormal_condition": "空调指示灯亮起，出风口打开或有气流吹出",
                "ai_supported": True,
                "enabled": True,
                "sort_order": 2,
            },
            {
                "indicator_code": "I003",
                "indicator_name": "电脑显示器",
                "category": "DEVICE",
                "description": "检查会议终端显示器是否处于熄屏/关机状态",
                "normal_condition": "电脑显示屏黑屏熄灭，无画面投显",
                "abnormal_condition": "显示器亮屏，显示桌面、屏保或输入信号画面",
                "ai_supported": True,
                "enabled": True,
                "sort_order": 3,
            },
            {
                "indicator_code": "I004",
                "indicator_name": "投影仪",
                "category": "DEVICE",
                "description": "检查投影仪设备及电动幕布状态",
                "normal_condition": "投影仪镜头无光束，处于待机/关机状态，幕布已收起",
                "abnormal_condition": "投影仪处于开启投射状态，幕布展开且有投射光线",
                "ai_supported": True,
                "enabled": True,
                "sort_order": 4,
            },
            {
                "indicator_code": "I005",
                "indicator_name": "桌面",
                "category": "ENVIRONMENT",
                "description": "检查会议桌台面是否收拾整洁无遗留物",
                "normal_condition": "台面干净整洁，无水杯、水瓶、纸屑、外卖盒及私人杂物",
                "abnormal_condition": "台面散落杂物、未带走的饮料瓶、废纸或私人物品",
                "ai_supported": True,
                "enabled": True,
                "sort_order": 5,
            },
            {
                "indicator_code": "I006",
                "indicator_name": "椅子",
                "category": "ENVIRONMENT",
                "description": "检查参会座椅是否摆放归位",
                "normal_condition": "所有会议椅整齐推进会议桌下方，摆放排列规范有序",
                "abnormal_condition": "座椅随意拉出、倾斜扭转或阻挡走道未归位",
                "ai_supported": True,
                "enabled": True,
                "sort_order": 6,
            },
            {
                "indicator_code": "I007",
                "indicator_name": "白板",
                "category": "ENVIRONMENT",
                "description": "检查白板表面书写内容是否已擦拭干净",
                "normal_condition": "白板板面擦拭干净无大面积笔迹残留，笔擦摆放于托槽内",
                "abnormal_condition": "白板留有会议板书笔迹、污渍未清理，或板擦乱扔",
                "ai_supported": True,
                "enabled": True,
                "sort_order": 7,
            },
        ]

        indicators_map = {}
        for ind in indicator_data:
            existing = db.scalar(
                select(InspectionIndicator).where(
                    InspectionIndicator.indicator_code == ind["indicator_code"]
                )
            )
            if not existing:
                existing = InspectionIndicator(**ind)
                db.add(existing)
                db.commit()
                db.refresh(existing)
            indicators_map[ind["indicator_code"]] = existing
        print(f"✓ {len(indicators_map)} Inspection indicators ready.")

        # 4. Standard Photos (FRONT & REAR)
        front_photo = db.scalar(
            select(StandardPhoto).where(
                StandardPhoto.room_id == room_301.id,
                StandardPhoto.photo_type == "FRONT",
                StandardPhoto.version == 1,
            )
        )
        if not front_photo:
            front_photo = StandardPhoto(
                room_id=room_301.id,
                photo_type="FRONT",
                photo_url="/static/standards/RM301_FRONT.jpg",
                shoot_position="正门入口处地面定位标识A",
                camera_direction="正向对准主会议桌及前方幕布",
                version=1,
                status="ACTIVE",
            )
            db.add(front_photo)
            db.commit()
            db.refresh(front_photo)

        rear_photo = db.scalar(
            select(StandardPhoto).where(
                StandardPhoto.room_id == room_301.id,
                StandardPhoto.photo_type == "REAR",
                StandardPhoto.version == 1,
            )
        )
        if not rear_photo:
            rear_photo = StandardPhoto(
                room_id=room_301.id,
                photo_type="REAR",
                photo_url="/static/standards/RM301_REAR.jpg",
                shoot_position="主讲台发言席地面定位标识B",
                camera_direction="反向对准后排座席与入户门",
                version=1,
                status="ACTIVE",
            )
            db.add(rear_photo)
            db.commit()
            db.refresh(rear_photo)
        print("✓ Standard photos (FRONT, REAR) ready.")

        # 5. Photo Regions (Normalized Bounding Boxes 0~1)
        regions_data = [
            # FRONT Regions
            {
                "standard_photo_id": front_photo.id,
                "region_code": "FRONT_LIGHT",
                "region_name": "顶灯照明区域",
                "x": Decimal("0.100000"),
                "y": Decimal("0.000000"),
                "width": Decimal("0.800000"),
                "height": Decimal("0.250000"),
                "description": "会议室天花板吊顶照明灯管组",
            },
            {
                "standard_photo_id": front_photo.id,
                "region_code": "FRONT_PROJECTOR",
                "region_name": "投影仪与幕布区域",
                "x": Decimal("0.250000"),
                "y": Decimal("0.100000"),
                "width": Decimal("0.500000"),
                "height": Decimal("0.350000"),
                "description": "正前方主投影幕布及天花板投影镜头",
            },
            {
                "standard_photo_id": front_photo.id,
                "region_code": "FRONT_DESK",
                "region_name": "会议主桌面区域",
                "x": Decimal("0.150000"),
                "y": Decimal("0.450000"),
                "width": Decimal("0.700000"),
                "height": Decimal("0.350000"),
                "description": "中央大长条会议桌面，检查清洁与杂物",
            },
            {
                "standard_photo_id": front_photo.id,
                "region_code": "FRONT_CHAIRS",
                "region_name": "前排会议椅区域",
                "x": Decimal("0.050000"),
                "y": Decimal("0.550000"),
                "width": Decimal("0.900000"),
                "height": Decimal("0.400000"),
                "description": "主桌两侧座椅摆放归位",
            },
            {
                "standard_photo_id": front_photo.id,
                "region_code": "FRONT_WHITEBOARD",
                "region_name": "侧墙白板区域",
                "x": Decimal("0.020000"),
                "y": Decimal("0.250000"),
                "width": Decimal("0.200000"),
                "height": Decimal("0.450000"),
                "description": "左侧墙壁白板书写及清洁状态",
            },
            # REAR Regions
            {
                "standard_photo_id": rear_photo.id,
                "region_code": "REAR_AC",
                "region_name": "后墙空调区域",
                "x": Decimal("0.700000"),
                "y": Decimal("0.100000"),
                "width": Decimal("0.250000"),
                "height": Decimal("0.250000"),
                "description": "后部壁挂/吸顶空调面板指示灯与摆叶",
            },
            {
                "standard_photo_id": rear_photo.id,
                "region_code": "REAR_MONITOR",
                "region_name": "控制电脑显示器",
                "x": Decimal("0.350000"),
                "y": Decimal("0.450000"),
                "width": Decimal("0.300000"),
                "height": Decimal("0.350000"),
                "description": "发言台电脑显示屏亮灭状态",
            },
        ]

        region_objects = {}
        for reg in regions_data:
            existing = db.scalar(
                select(PhotoRegion).where(
                    PhotoRegion.standard_photo_id == reg["standard_photo_id"],
                    PhotoRegion.region_code == reg["region_code"],
                )
            )
            if not existing:
                existing = PhotoRegion(**reg)
                db.add(existing)
                db.commit()
                db.refresh(existing)
            region_objects[reg["region_code"]] = existing
        print(f"✓ {len(region_objects)} Photo regions configured.")

        # 6. Bind Room Indicators (MeetingRoom 301 <-> Indicators & Regions)
        indicator_region_mapping = [
            ("I001", "FRONT_LIGHT", "关闭"),
            ("I002", "REAR_AC", "关闭"),
            ("I003", "REAR_MONITOR", "黑屏关闭"),
            ("I004", "FRONT_PROJECTOR", "关闭待机"),
            ("I005", "FRONT_DESK", "整洁无杂物"),
            ("I006", "FRONT_CHAIRS", "整齐推入归位"),
            ("I007", "FRONT_WHITEBOARD", "擦拭干净"),
        ]

        for ind_code, reg_code, std_val in indicator_region_mapping:
            ind = indicators_map[ind_code]
            reg = region_objects[reg_code]
            existing = db.scalar(
                select(RoomIndicator).where(
                    RoomIndicator.room_id == room_301.id,
                    RoomIndicator.indicator_id == ind.id,
                )
            )
            if not existing:
                link = RoomIndicator(
                    room_id=room_301.id,
                    indicator_id=ind.id,
                    region_id=reg.id,
                    standard_value=std_val,
                    enabled=True,
                    sort_order=ind.sort_order,
                )
                db.add(link)
        db.commit()
        print("✓ Room indicators successfully bound.")

        print("\nAll seed data initialized successfully! 🎉")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
