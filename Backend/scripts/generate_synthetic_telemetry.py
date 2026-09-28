"""
SafeGas AI Synthetic Telemetry Generator

Generates realistic historical LPG cylinder weight readings, gas PPM sensor data,
and leak events for development and analytics testing.

Architecture Guardrails:
- Telemetry is written directly to PostgreSQL database models (WeightReading, GasReading, LeakEvent).
- The Analytics Service processes this telemetry independently.
- Idempotent device/cylinder resolution avoids duplicate device creation.
- Strict user data isolation: each user's telemetry is bound exclusively to their device.

Usage:
    # Single target user:
    python scripts/generate_synthetic_telemetry.py --user-email "rahul.demo@kitchen.ai" --device-id "DEV_KITCHEN_01" --days 30

    # All registered users (reusing existing devices, or creating test devices with --create-test-data):
    python scripts/generate_synthetic_telemetry.py --all-users --days 30 --create-test-data
"""

import sys
import argparse
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, '.')

from app.db.database import SessionLocal
from app.models.user import User
from app.models.device import Device
from app.models.cylinder import Cylinder
from app.models.weight_reading import WeightReading
from app.models.gas_reading import GasReading
from app.models.leak_event import LeakEvent
from app.core.security import hash_password


def parse_args():
    parser = argparse.ArgumentParser(description="Generate synthetic LPG telemetry for SafeGas AI testing.")
    parser.add_argument("--all-users", action="store_true", help="Generate synthetic telemetry for ALL registered users.")
    parser.add_argument("--user-email", type=str, default=None, help="Target specific user email address.")
    parser.add_argument("--device-id", type=str, default=None, help="Target specific device ID.")
    parser.add_argument("--days", type=int, default=30, help="Number of past days of telemetry to generate (default: 30).")
    parser.add_argument("--readings-per-day", type=int, default=24, help="Readings per day (default: 24, one per hour).")
    parser.add_argument("--create-test-data", action="store_true", help="Auto-create test device/cylinder if user has none.")
    parser.add_argument("--force", action="store_true", help="Force regeneration even if telemetry already exists.")
    return parser.parse_args()


def device_has_telemetry(db, device_id: str) -> bool:
    """Returns True if the target device already has recorded telemetry."""
    return db.query(WeightReading).filter(WeightReading.device_id == device_id).count() > 0


def initialize_demo_data_for_user(
    db,
    user_id: int,
    days: int = 30,
    readings_per_day: int = 24,
    force_regenerate: bool = False,
) -> str:
    """
    Safely and idempotently initializes demo device, cylinder, and synthetic telemetry for a user.
    Returns status: 'initialized', 'already_initialized', 'demo_disabled', or 'user_not_found'.
    """
    from app.core.config import settings
    if not getattr(settings, "SAFEGAS_DEMO_MODE", True):
        print(f"[DEMO] Demo mode disabled (SAFEGAS_DEMO_MODE=false). Skipping demo telemetry for user id={user_id}.")
        return "demo_disabled"

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return "user_not_found"

    device, cylinder, _, _ = resolve_device_and_cylinder_for_user(
        db, user=user, create_test_data=True
    )
    if not device or not cylinder:
        return "device_resolution_failed"

    if not force_regenerate and device_has_telemetry(db, device.id):
        print(f"[DEMO] Synthetic telemetry already exists for user {user.email} (Device: {device.id}). Skipping ...")
        return "already_initialized"

    w_cnt, g_cnt, l_cnt = generate_telemetry_for_device(
        db, user=user, device=device, cylinder=cylinder, days=days, readings_per_day=readings_per_day
    )
    print(f"[DEMO] Initialized synthetic telemetry for user {user.email} (Device: {device.id}, Readings: {w_cnt} weight, {g_cnt} gas, {l_cnt} leaks)")
    return "initialized"


def resolve_device_and_cylinder_for_user(db, user: User, custom_device_id: str = None, create_test_data: bool = False):
    """
    Idempotently resolves or creates a device and cylinder for a given user.
    Prevents creating duplicate devices for the same user upon multiple runs.
    """
    device = None
    created_device = False
    created_cylinder = False

    # 1. If explicit device_id supplied, look up
    if custom_device_id:
        device = db.query(Device).filter(Device.id == custom_device_id).first()

    # 2. Look up existing device owned by this user
    if not device:
        device = db.query(Device).filter(Device.user_id == user.id).first()

    # 3. Check deterministic simulated device ID format: SIM_<user_id:02d>_01
    deterministic_id = f"SIM_{user.id:02d}_01"
    if not device:
        device = db.query(Device).filter(Device.id == deterministic_id).first()
        if device and device.user_id != user.id:
            device.user_id = user.id
            db.commit()

    # 4. If still no device, create ONE if --create-test-data flag is provided
    if not device:
        if create_test_data:
            target_id = custom_device_id or deterministic_id
            device = Device(
                id=target_id,
                user_id=user.id,
                name=f"Kitchen Gas Scale ({user.name.split()[0]})",
                firmware_version="v2.1.0-sim",
                status="online",
                paired_at=datetime.now(timezone.utc) - timedelta(days=90),
            )
            db.add(device)
            db.commit()
            db.refresh(device)
            created_device = True
        else:
            return None, None, False, False

    # 5. Resolve or create cylinder for the resolved device
    cylinder = db.query(Cylinder).filter(Cylinder.device_id == device.id).first()
    if not cylinder and create_test_data:
        cylinder = Cylinder(
            device_id=device.id,
            tare_weight_g=15300.0,
            full_weight_g=29500.0,
            cylinder_type="14.2kg",
            install_date=datetime.now(timezone.utc) - timedelta(days=40),
        )
        db.add(cylinder)
        db.commit()
        db.refresh(cylinder)
        created_cylinder = True

    return device, cylinder, created_device, created_cylinder


def generate_telemetry_for_device(db, user: User, device: Device, cylinder: Cylinder, days: int, readings_per_day: int):
    """
    Generates realistic weight readings, gas readings, and leak events for a specific user device.
    Introduces controlled user-specific variation based on user.id.
    """
    now = datetime.now(timezone.utc)
    start_date = now - timedelta(days=days)

    # Clean existing telemetry in target window for this device to prevent duplicate overlapping readings
    db.query(WeightReading).filter(
        WeightReading.device_id == device.id,
        WeightReading.timestamp >= start_date,
    ).delete()
    db.query(GasReading).filter(
        GasReading.device_id == device.id,
        GasReading.timestamp >= start_date,
    ).delete()
    db.query(LeakEvent).filter(
        LeakEvent.device_id == device.id,
        LeakEvent.start_time >= start_date,
    ).delete()
    db.commit()

    # User-specific variation parameters
    user_rng = random.Random(user.id * 1000 + 42)
    
    # Controlled variation: starting cylinder weight (between 25,000g and 29,500g)
    start_offset = (user.id % 4) * 1100.0
    full_g = cylinder.full_weight_g if cylinder else 29500.0
    tare_g = cylinder.tare_weight_g if cylinder else 15300.0
    current_weight_g = max(tare_g + 2000.0, full_g - start_offset)

    # Controlled variation: daily cooking intensity multiplier (0.85x to 1.25x)
    intensity_mult = 0.85 + ((user.id * 7) % 40) / 100.0

    # Controlled variation: number of leak test events for this user (0, 1, or 2)
    num_leak_events = (user.id * 7 + 1) % 3
    leak_day_offsets = set(user_rng.sample(range(2, days - 1), min(num_leak_events, days - 2))) if days > 5 else set()

    weight_objects = []
    gas_objects = []
    leak_objects = []

    interval_minutes = int(1440 / readings_per_day)

    for day_offset in range(days):
        current_day_date = (start_date + timedelta(days=day_offset)).date()

        # Simulate refill if weight drops near empty (< 500g remaining LPG)
        if current_weight_g < (tare_g + 500.0):
            current_weight_g = full_g

        is_leak_day = day_offset in leak_day_offsets

        for r_idx in range(readings_per_day):
            timestamp = datetime(
                current_day_date.year,
                current_day_date.month,
                current_day_date.day,
                tzinfo=timezone.utc
            ) + timedelta(minutes=r_idx * interval_minutes)

            hour = timestamp.hour

            # Time-of-day cooking drops with user intensity multiplier
            drop = 0.0
            if 7 <= hour <= 8:
                # Morning (Breakfast)
                drop = user_rng.uniform(70.0, 140.0) * intensity_mult
            elif 12 <= hour <= 13:
                # Afternoon (Lunch)
                drop = user_rng.uniform(50.0, 110.0) * intensity_mult
            elif 19 <= hour <= 20:
                # Evening (Dinner)
                drop = user_rng.uniform(100.0, 190.0) * intensity_mult
            else:
                # Idle sensor noise (-2g to +2g)
                drop = user_rng.uniform(-2.0, 2.0)

            current_weight_g = max(tare_g, current_weight_g - drop)

            weight_objects.append(
                WeightReading(
                    device_id=device.id,
                    weight_g=round(current_weight_g, 2),
                    timestamp=timestamp,
                )
            )

            # Gas PPM sensor reading
            base_ppm = user_rng.uniform(110.0, 185.0)
            if is_leak_day and hour == 19 and r_idx % 2 == 0:
                base_ppm = user_rng.uniform(430.0, 680.0)

            status_str = "normal" if base_ppm < 300 else "warning" if base_ppm < 500 else "critical"

            gas_objects.append(
                GasReading(
                    device_id=device.id,
                    ppm_value=round(base_ppm, 2),
                    status=status_str,
                    timestamp=timestamp,
                )
            )

        if is_leak_day:
            leak_start = datetime(
                current_day_date.year,
                current_day_date.month,
                current_day_date.day,
                19, 15,
                tzinfo=timezone.utc
            )
            leak_objects.append(
                LeakEvent(
                    device_id=device.id,
                    start_time=leak_start,
                    end_time=leak_start + timedelta(minutes=20),
                    peak_ppm=round(user_rng.uniform(520.0, 710.0), 1),
                    auto_shutoff_triggered=True,
                    false_alarm=False,
                )
            )

    db.bulk_save_objects(weight_objects)
    db.bulk_save_objects(gas_objects)
    db.bulk_save_objects(leak_objects)
    db.commit()

    return len(weight_objects), len(gas_objects), len(leak_objects)


def main():
    args = parse_args()
    db = SessionLocal()

    try:
        if args.all_users:
            users = db.query(User).order_by(User.id).all()
        elif args.user_email:
            user = db.query(User).filter(User.email == args.user_email.strip().lower()).first()
            users = [user] if user else []
        else:
            # Default to first user
            user = db.query(User).first()
            users = [user] if user else []

        if not users:
            print("[ERROR] No matching users found in database.")
            sys.exit(1)

        users_processed = 0
        users_with_existing_devices = 0
        devices_created = 0
        cylinders_created = 0

        summary_rows = []
        total_weight_count = 0
        total_gas_count = 0
        total_leak_count = 0

        for u in users:
            existing_dev = db.query(Device).filter(Device.user_id == u.id).first()
            if existing_dev:
                users_with_existing_devices += 1

            device, cylinder, dev_created, cyl_created = resolve_device_and_cylinder_for_user(
                db,
                user=u,
                custom_device_id=args.device_id if len(users) == 1 else None,
                create_test_data=args.create_test_data,
            )

            if dev_created:
                devices_created += 1
            if cyl_created:
                cylinders_created += 1

            if not device or not cylinder:
                print(f"[SKIP] User {u.email} (ID: {u.id}) has no device. Pass --create-test-data to create test devices.")
                continue

            if not args.force and device_has_telemetry(db, device.id):
                print(f"[DEMO] Synthetic telemetry already exists for user {u.email} (Device: {device.id}). Skipping ...")
                continue

            w_cnt, g_cnt, l_cnt = generate_telemetry_for_device(
                db,
                user=u,
                device=device,
                cylinder=cylinder,
                days=args.days,
                readings_per_day=args.readings_per_day,
            )

            users_processed += 1
            total_weight_count += w_cnt
            total_gas_count += g_cnt
            total_leak_count += l_cnt

            summary_rows.append({
                "email": u.email,
                "device_id": device.id,
                "weight_count": w_cnt,
                "gas_count": g_cnt,
                "leak_count": l_cnt,
            })

        print("\nSafeGas AI Synthetic Telemetry Generation")
        print("==================================================")
        print(f"Users processed            : {users_processed}")
        print(f"Users with existing devices: {users_with_existing_devices}")
        print(f"Devices created            : {devices_created}")
        print(f"Cylinders created          : {cylinders_created}")
        print("\nTelemetry generated:\n")
        print(f"{'User Email':<36} {'Device ID':<18} {'Weight':<9} {'Gas':<7} {'Leaks':<6}")
        print("-" * 78)
        for r in summary_rows:
            print(f"{r['email']:<36} {r['device_id']:<18} {r['weight_count']:<9} {r['gas_count']:<7} {r['leak_count']:<6}")
        print("-" * 78)
        print("Total:")
        print(f"Weight readings: {total_weight_count}")
        print(f"Gas readings   : {total_gas_count}")
        print(f"Leak events    : {total_leak_count}\n")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Telemetry generation failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    main()
