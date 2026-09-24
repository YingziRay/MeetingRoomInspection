import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.standard_photo import StandardPhoto
from sqlalchemy import select


def create_standards():
    standards_dir = Path(settings.upload_dir) / "standards"
    standards_dir.mkdir(parents=True, exist_ok=True)

    # 1. Generate FRONT standard image (1280x720)
    front_img = Image.new("RGB", (1280, 720), color=(240, 242, 245))
    draw = ImageDraw.Draw(front_img)
    # Background ceiling
    draw.rectangle([(0, 0), (1280, 200)], fill=(225, 230, 235))
    # Lights
    draw.rectangle([(150, 20), (1130, 100)], outline=(200, 200, 200), width=3, fill=(255, 255, 240))
    draw.text((560, 50), "Ceiling Lights [OFF]", fill=(100, 100, 100))
    # Projector Screen
    draw.rectangle([(350, 90), (930, 320)], outline=(120, 120, 120), width=4, fill=(210, 215, 220))
    draw.text((540, 190), "Projector Screen [Retracted]", fill=(80, 80, 80))
    # Main Conference Table
    draw.polygon([(200, 420), (1080, 420), (1200, 680), (80, 680)], fill=(180, 150, 120))
    draw.text((550, 530), "Conference Table [Clean]", fill=(60, 40, 20))
    # Chairs
    draw.rectangle([(120, 440), (220, 560)], fill=(100, 110, 120))
    draw.rectangle([(1060, 440), (1160, 560)], fill=(100, 110, 120))
    draw.text((130, 490), "Chairs", fill=(255, 255, 255))
    # Whiteboard on Left Wall
    draw.rectangle([(30, 200), (180, 420)], outline=(90, 90, 90), width=3, fill=(255, 255, 255))
    draw.text((50, 300), "Whiteboard\n [Clean]", fill=(50, 50, 50))

    front_path = standards_dir / "RM301_FRONT.jpg"
    front_img.save(front_path, "JPEG", quality=95)
    print(f"✓ Saved FRONT standard photo: {front_path}")

    # 2. Generate REAR standard image (1280x720)
    rear_img = Image.new("RGB", (1280, 720), color=(240, 242, 245))
    draw_rear = ImageDraw.Draw(rear_img)
    # Background ceiling
    draw_rear.rectangle([(0, 0), (1280, 200)], fill=(225, 230, 235))
    # Rear Door
    draw_rear.rectangle([(480, 220), (800, 680)], outline=(100, 80, 60), width=4, fill=(215, 195, 175))
    draw_rear.text((590, 420), "Entrance Door", fill=(80, 60, 40))
    # AC unit on wall
    draw_rear.rectangle([(920, 80), (1220, 220)], outline=(160, 160, 160), width=3, fill=(250, 250, 250))
    draw_rear.text((1010, 140), "Air Conditioner [OFF]", fill=(90, 90, 90))
    # Podium / Monitor
    draw_rear.rectangle([(440, 380), (840, 620)], outline=(110, 110, 110), width=3, fill=(50, 50, 55))
    draw_rear.text((570, 480), "Podium Monitor [OFF]", fill=(200, 200, 200))

    rear_path = standards_dir / "RM301_REAR.jpg"
    rear_img.save(rear_path, "JPEG", quality=95)
    print(f"✓ Saved REAR standard photo: {rear_path}")

    # 3. Update database URL in standard_photo
    db = SessionLocal()
    try:
        front_std = db.scalar(select(StandardPhoto).where(StandardPhoto.photo_type == "FRONT"))
        if front_std:
            front_std.photo_url = "/uploads/standards/RM301_FRONT.jpg"

        rear_std = db.scalar(select(StandardPhoto).where(StandardPhoto.photo_type == "REAR"))
        if rear_std:
            rear_std.photo_url = "/uploads/standards/RM301_REAR.jpg"

        db.commit()
        print("✓ Updated standard_photo URLs in DB to /uploads/standards/...")
    finally:
        db.close()


if __name__ == "__main__":
    create_standards()
