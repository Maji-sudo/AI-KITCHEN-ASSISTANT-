import random
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.device import Device
from app.models.cylinder import Cylinder
from app.models.dish import Dish
from app.models.gas_reading import GasReading
from app.models.weight_reading import WeightReading
from app.models.leak_event import LeakEvent
from app.models.usage_analytics import UsageAnalytics
from app.models.refill_prediction import RefillPrediction
from app.models.cooking_history import CookingHistory

from app.schemas.telemetry import GasReadingCreate, WeightReadingCreate, LeakEventCreate
from app.schemas.cooking import CookingHistoryCreate
from app.services.telemetry_service import telemetry_service
from app.services.cooking_service import cooking_service
from app.services.analytics_service import analytics_service
from app.services.refill_service import refill_service


class SimulationService:
    """
    SafeGas AI Development Data Simulator & Ingestion Engine.
    Routes data through the exact same ingestion and analytics services
    used by future IoT hardware.
    """

    def create_simulated_device(
        self,
        db: Session,
        user_id: int,
        name: str = "Kitchen SafeGas Hub",
        cylinder_type: str = "14.2kg",
        custom_id: Optional[str] = None
    ) -> Device:
        """Create a simulated SafeGas device paired to user_id with attached standard cylinder."""
        device_id = custom_id or f"SGD-SIM-{random.randint(1000, 9999)}"

        # Check existing device
        existing = db.query(Device).filter(Device.id == device_id).first()
        if existing:
            return existing

        device = Device(
            id=device_id,
            user_id=user_id,
            name=name,
            firmware_version="1.2.0-sim",
            status="active",
            signal_strength=96,
            battery_level=98,
        )
        db.add(device)
        db.commit()
        db.refresh(device)

        # Standard Indian LPG Cylinder specs
        # Tare (empty): 15,300g, Full gross: 29,500g, Net LPG: 14,200g
        cylinder = Cylinder(
            device_id=device_id,
            tare_weight_g=15300.0,
            full_weight_g=29500.0,
            cylinder_type=cylinder_type,
            install_date=datetime.now(timezone.utc)
        )
        db.add(cylinder)
        db.commit()

        # Seed initial full cylinder weight reading via telemetry service
        initial_weight = WeightReadingCreate(
            device_id=device_id,
            weight_g=29500.0,
            timestamp=datetime.now(timezone.utc) - timedelta(days=14)
        )
        telemetry_service.record_weight_reading(db, reading_in=initial_weight)

        # Seed initial normal baseline gas reading
        initial_gas = GasReadingCreate(
            device_id=device_id,
            ppm_value=182.0,
            status="normal",
            timestamp=datetime.now(timezone.utc)
        )
        telemetry_service.record_gas_reading(db, reading_in=initial_gas)

        return device

    def generate_usage_simulation(
        self,
        db: Session,
        device_id: str,
        user_id: int,
        days: int = 7,
        pattern: str = "medium"
    ) -> Dict[str, Any]:
        """
        Generates realistic multi-day LPG weight, consumption, cooking, and gas telemetry.
        Enforces realistic invariant:
        previous cylinder weight - LPG consumed = new cylinder weight.
        """
        cylinder = db.query(Cylinder).filter(Cylinder.device_id == device_id).first()
        tare_weight = cylinder.tare_weight_g if cylinder else 15300.0
        full_weight = cylinder.full_weight_g if cylinder else 29500.0
        net_lpg = full_weight - tare_weight  # 14200g

        # Fetch latest weight reading or start at full
        latest_weight_objs = db.query(WeightReading).filter(
            WeightReading.device_id == device_id
        ).order_by(WeightReading.timestamp.desc()).limit(1).all()

        current_weight = latest_weight_objs[0].weight_g if latest_weight_objs else full_weight

        # Fetch sample dishes from DB or fallbacks
        dishes = db.query(Dish).all()
        dish_map = [
            {"name": d.dish_name, "id": d.id, "gas": d.base_gas_g, "dur": d.base_duration_min}
            for d in dishes
        ] if dishes else [
            {"name": "Tea & Toast", "id": None, "gas": 30.0, "dur": 10},
            {"name": "Dal Tadka & Rice", "id": None, "gas": 95.0, "dur": 30},
            {"name": "Roti & Sabzi", "id": None, "gas": 110.0, "dur": 35},
            {"name": "Khichdi", "id": None, "gas": 60.0, "dur": 20},
        ]

        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=days)

        readings_generated = 0
        cooking_sessions_generated = 0
        weight_progression = []

        for d in range(days):
            day_date = start_date + timedelta(days=d)
            is_weekend = day_date.weekday() >= 5

            # Target daily consumption based on pattern
            if pattern == "low":
                base_burn = random.uniform(180.0, 230.0)
            elif pattern == "high":
                base_burn = random.uniform(480.0, 580.0)
            elif pattern == "weekend-heavy":
                base_burn = random.uniform(450.0, 560.0) if is_weekend else random.uniform(200.0, 260.0)
            elif pattern == "irregular":
                base_burn = random.uniform(150.0, 520.0)
            else:  # medium / normal
                base_burn = random.uniform(310.0, 370.0)

            # Split daily burn across 2-3 cooking sessions
            num_meals = random.choice([2, 3])
            portions = [random.uniform(0.7, 1.3) for _ in range(num_meals)]
            portion_sum = sum(portions)
            meal_burns = [(p / portion_sum) * base_burn for p in portions]

            meal_times = [
                day_date.replace(hour=8, minute=random.randint(0, 45)),
                day_date.replace(hour=13, minute=random.randint(0, 45)),
                day_date.replace(hour=20, minute=random.randint(0, 45)),
            ][:num_meals]

            day_consumed = 0.0

            for i, meal_burn in enumerate(meal_burns):
                meal_time = meal_times[i]
                dish_choice = random.choice(dish_map)

                # 1. Record cooking session
                cook_session = CookingHistoryCreate(
                    user_id=user_id,
                    device_id=device_id,
                    dish_id=dish_choice["id"],
                    logged_date=meal_time,
                    actual_gas_g=round(meal_burn, 1),
                    actual_duration_min=dish_choice["dur"] + random.randint(-3, 8)
                )
                cooking_service.record_cooking_session(db, session_in=cook_session)
                cooking_sessions_generated += 1
                day_consumed += meal_burn

                # 2. Update cylinder weight: previous - consumed
                current_weight = max(tare_weight + 50.0, current_weight - meal_burn)

                # Ingest weight reading via telemetry service
                weight_in = WeightReadingCreate(
                    device_id=device_id,
                    weight_g=round(current_weight, 1),
                    timestamp=meal_time + timedelta(minutes=dish_choice["dur"])
                )
                telemetry_service.record_weight_reading(db, reading_in=weight_in)
                readings_generated += 1

                # 3. Ingest realistic normal gas reading (around 175-195 PPM)
                gas_in = GasReadingCreate(
                    device_id=device_id,
                    ppm_value=round(random.uniform(178.0, 194.0), 1),
                    status="normal",
                    timestamp=meal_time + timedelta(minutes=15),
                    source="SIMULATOR",
                )
                telemetry_service.record_gas_reading(db, reading_in=gas_in)
                readings_generated += 1

            # 4. Calculate analytics for this day
            day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            try:
                analytics_service.calculate_and_record_usage(
                    db,
                    device_id=device_id,
                    start_time=day_start,
                    end_time=day_end,
                    period_type="daily"
                )
            except Exception:
                pass

            remaining_net = max(0.0, current_weight - tare_weight)
            weight_progression.append({
                "day": day_date.strftime("%Y-%m-%d"),
                "total_weight_g": round(current_weight, 1),
                "remaining_net_g": round(remaining_net, 1),
                "consumed_g": round(day_consumed, 1)
            })

        # 5. Automatically compute updated refill prediction
        refill_pred = refill_service.compute_refill_prediction(db, device_id=device_id)

        return {
            "days_simulated": days,
            "pattern": pattern,
            "cooking_sessions": cooking_sessions_generated,
            "telemetry_readings": readings_generated,
            "current_weight_g": round(current_weight, 1),
            "remaining_lpg_g": round(max(0.0, current_weight - tare_weight), 1),
            "refill_days_left": refill_pred.days_left,
            "predicted_empty_date": refill_pred.predicted_empty_date.isoformat(),
            "progression": weight_progression[-5:]
        }

    def generate_safety_scenario(
        self,
        db: Session,
        device_id: str,
        user_id: int,
        scenario: str = "normal"
    ) -> Dict[str, Any]:
        """
        Simulate gas sensor scenarios:
        - NORMAL: 180 -> 185 -> 190 -> 187
        - WARNING: 220 -> 270 -> 320 -> 350
        - CRITICAL: 250 -> 450 -> 700 -> 1000 (triggers LeakEvent + auto shutoff)
        """
        now = datetime.now(timezone.utc)

        if scenario == "warning":
            ppm_sequence = [450.0, 550.0, 680.0, 750.0]
        elif scenario == "critical":
            ppm_sequence = [600.0, 850.0, 1050.0, 1100.0]
        else:  # normal
            ppm_sequence = [170.0, 185.0, 190.0, 180.0]

        recorded_readings = []
        for i, ppm in enumerate(ppm_sequence):
            reading_time = now - timedelta(seconds=(len(ppm_sequence) - i) * 10)
            reading_in = GasReadingCreate(
                device_id=device_id,
                ppm_value=ppm,
                timestamp=reading_time,
                source="SIMULATOR",
            )
            # telemetry_service auto-classifies status and handles warnings/critical leaks
            saved = telemetry_service.record_gas_reading(db, reading_in=reading_in)
            recorded_readings.append({
                "ppm": saved.ppm_value,
                "status": saved.status,
                "timestamp": saved.timestamp.isoformat()
            })

        return {
            "scenario": scenario,
            "sequence": recorded_readings,
            "latest_ppm": recorded_readings[-1]["ppm"],
            "latest_status": recorded_readings[-1]["status"]
        }

    def reset_simulated_data(
        self,
        db: Session,
        device_id: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Reset simulated readings for a device back to a clean initial state.
        Preserves the device record.
        """
        db.query(GasReading).filter(GasReading.device_id == device_id).delete()
        db.query(WeightReading).filter(WeightReading.device_id == device_id).delete()
        db.query(LeakEvent).filter(LeakEvent.device_id == device_id).delete()
        db.query(UsageAnalytics).filter(UsageAnalytics.device_id == device_id).delete()
        db.query(RefillPrediction).filter(RefillPrediction.device_id == device_id).delete()
        db.query(CookingHistory).filter(
            CookingHistory.device_id == device_id,
            CookingHistory.user_id == user_id
        ).delete()
        db.commit()

        # Seed fresh baseline
        init_weight = WeightReadingCreate(
            device_id=device_id,
            weight_g=29500.0,
            timestamp=datetime.now(timezone.utc)
        )
        telemetry_service.record_weight_reading(db, reading_in=init_weight)

        init_gas = GasReadingCreate(
            device_id=device_id,
            ppm_value=180.0,
            status="normal",
            timestamp=datetime.now(timezone.utc),
            source="SIMULATOR",
        )
        telemetry_service.record_gas_reading(db, reading_in=init_gas)
        refill_service.compute_refill_prediction(db, device_id=device_id)

        return {"reset_completed": True, "device_id": device_id}


simulation_service = SimulationService()
