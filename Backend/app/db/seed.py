"""
Database Seed Script — populates SQLite database with rich demo data for local development & frontend testing.
Run with: python -m app.db.seed
"""
import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
import app.db.base  # Register all models for SQLAlchemy mapper resolution
from app.models.user import User
from app.models.device import Device
from app.models.cylinder import Cylinder
from app.models.dish import Dish
from app.models.cooking_history import CookingHistory
from app.models.gas_reading import GasReading
from app.models.weight_reading import WeightReading
from app.models.leak_event import LeakEvent
from app.models.usage_analytics import UsageAnalytics
from app.models.efficiency_score import EfficiencyScore
from app.models.recommendation import Recommendation
from app.models.notification import Notification
from app.models.booking import Booking


def seed_database():
    print("--- Seeding database with initial demo data ---")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Seed Dish Library
        if db.query(Dish).count() == 0:
            dishes = [
                Dish(dish_name="Paneer Butter Masala", cuisine_tag="North Indian", base_gas_g=120.0, base_duration_min=25),
                Dish(dish_name="Dal Tadka", cuisine_tag="North Indian", base_gas_g=80.0, base_duration_min=20),
                Dish(dish_name="Masala Chai (4 Cups)", cuisine_tag="Beverage", base_gas_g=25.0, base_duration_min=8),
                Dish(dish_name="Chicken Biryani", cuisine_tag="Hyderabadi", base_gas_g=210.0, base_duration_min=45),
                Dish(dish_name="Phulka / Chapati (10 pcs)", cuisine_tag="Indian Staple", base_gas_g=60.0, base_duration_min=15),
            ]
            db.add_all(dishes)
            print("  [+] Added 5 dishes to library")

        # 2. Seed Demo User
        user = db.query(User).filter(User.phone == "+919876543210").first()
        if not user:
            user = User(
                name="Chef Rahul",
                phone="+919876543210",
                email="rahul.demo@kitchen.ai",
                language_pref="en",
            )
            db.add(user)
            db.flush()
            print(f"  [+] Created Demo User (ID: {user.id})")

        # 3. Seed Demo Device & Cylinder
        device = db.query(Device).filter(Device.id == "DEV_KITCHEN_01").first()
        if not device:
            device = Device(
                id="DEV_KITCHEN_01",
                user_id=user.id,
                name="Main Gas Scale (Kitchen)",
                firmware_version="v2.1.0",
                status="online",
            )
            db.add(device)
            db.flush()

            cylinder = Cylinder(
                device_id=device.id,
                tare_weight_g=15300.0,
                full_weight_g=14200.0,
                cylinder_type="14.2kg",
            )
            db.add(cylinder)
            print(f"  [+] Created Demo Device ({device.id}) and Cylinder")

        # 4. Seed Telemetry Data (Gas & Weight)
        now = datetime.datetime.now(datetime.timezone.utc)
        if db.query(GasReading).filter(GasReading.device_id == device.id).count() == 0:
            gas_readings = [
                GasReading(device_id=device.id, ppm_value=12.5, status="normal", timestamp=now - datetime.timedelta(minutes=30)),
                GasReading(device_id=device.id, ppm_value=14.0, status="normal", timestamp=now - datetime.timedelta(minutes=15)),
                GasReading(device_id=device.id, ppm_value=18.2, status="normal", timestamp=now - datetime.timedelta(minutes=5)),
            ]
            db.add_all(gas_readings)

            weight_readings = [
                WeightReading(device_id=device.id, weight_g=24500.0, timestamp=now - datetime.timedelta(hours=2)),
                WeightReading(device_id=device.id, weight_g=24420.0, timestamp=now - datetime.timedelta(hours=1)),
                WeightReading(device_id=device.id, weight_g=24350.0, timestamp=now),
            ]
            db.add_all(weight_readings)
            print("  [+] Added sample gas & weight telemetry readings")

        # 5. Seed Usage Analytics & Efficiency Score
        if db.query(UsageAnalytics).filter(UsageAnalytics.device_id == device.id).count() == 0:
            analytics = UsageAnalytics(
                device_id=device.id,
                period_type="daily",
                period_start=now - datetime.timedelta(days=1),
                consumption_g=350.0,
                avg_rate=14.58,
                anomaly_flag=False,
                forecast_next_g=360.0,
            )
            db.add(analytics)

            score = EfficiencyScore(
                device_id=device.id,
                period_type="weekly",
                overall_score=88.5,
                component_scores_json={
                    "safety": 95.0,
                    "gas_efficiency": 85.0,
                    "cooking_efficiency": 88.0,
                    "cylinder_utilization": 86.0
                },
            )
            db.add(score)
            print("  [+] Added sample analytics & efficiency scores")

        # 6. Seed Sample Recommendation & Notification
        if db.query(Recommendation).filter(Recommendation.device_id == device.id).count() == 0:
            rec = Recommendation(
                user_id=user.id,
                device_id=device.id,
                category="efficiency",
                message="Covering pots while boiling water can save up to 15% gas per session.",
                supporting_facts_json={"estimated_saving_g": 35.0},
                confidence=0.92,
                status="active",
            )
            db.add(rec)

            notif = Notification(
                user_id=user.id,
                channel="fcm",
                payload={"title": "Weekly Efficiency Report", "body": "Your kitchen efficiency score was 88.5/100 this week!"},
                delivery_status="delivered",
                sent_at=now - datetime.timedelta(hours=6),
            )
            db.add(notif)
            print("  [+] Added sample recommendation & notification")

        db.commit()
        print("\n[SUCCESS] Database seed complete! Demo data is ready.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
