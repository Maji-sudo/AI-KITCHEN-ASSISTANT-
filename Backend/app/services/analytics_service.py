from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from app.repositories.telemetry_repository import weight_reading_repo
from app.repositories.efficiency_repository import usage_analytics_repo

from app.schemas.analytics import (
    UsageAnalyticsCreate,
    UsageAnalyticsResponse,
    AnalyticsSummary,
)

from app.models.usage_analytics import UsageAnalytics


class AnalyticsService:

    # ==========================================================
    # RECORD ANALYTICS
    # ==========================================================

    def record_usage(
        self,
        db: Session,
        analytics_in: UsageAnalyticsCreate
    ) -> UsageAnalytics:
        """
        Save an already-calculated analytics record.
        """

        return usage_analytics_repo.create(
            db,
            obj_in=analytics_in
        )

    # ==========================================================
    # GET DEVICE ANALYTICS
    # ==========================================================

    def get_device_analytics(
        self,
        db: Session,
        device_id: str,
        period_type: str = "daily",
        limit: int = 30
    ) -> List[UsageAnalytics]:
        """
        Retrieve analytics records for a device.

        period_type:
            daily
            weekly
            monthly
        """

        return usage_analytics_repo.get_by_period_type(
            db,
            device_id=device_id,
            period_type=period_type,
            limit=limit
        )

    # ==========================================================
    # GET WEIGHT READINGS
    # ==========================================================

    def _get_weight_readings(
        self,
        db: Session,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
    ):
        """
        Retrieve weight readings for a specific time period.

        This is kept as a private helper because the repository
        is responsible for database access.
        """

        return weight_reading_repo.get_for_period(
            db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )

    # ==========================================================
    # CALCULATE GAS CONSUMPTION
    # ==========================================================

    def calculate_consumption(
        self,
        db: Session,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """
        Calculate total gas consumed during a period.

        Consumption is calculated from decreases in cylinder weight.

        Example:

            14000 g
            13800 g  -> 200 g consumed
            13500 g  -> 300 g consumed
            13300 g  -> 200 g consumed

            Total = 700 g
        """

        readings = self._get_weight_readings(
            db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )

        if len(readings) < 2:
            return 0.0

        consumption = 0.0

        for previous, current in zip(readings, readings[1:]):

            difference = previous.weight_g - current.weight_g

            # Weight decreased → gas was consumed.
            if difference > 0:
                consumption += difference

        return float(consumption)

    # ==========================================================
    # CALCULATE AVERAGE CONSUMPTION RATE
    # ==========================================================

    def calculate_average_rate(
        self,
        db: Session,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> float:
        """
        Calculate average gas consumption rate in grams/hour.
        """

        consumption = self.calculate_consumption(
            db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )

        duration_seconds = (
            end_time - start_time
        ).total_seconds()

        if duration_seconds <= 0:
            return 0.0

        duration_hours = duration_seconds / 3600

        return float(
            consumption / duration_hours
        )

    # ==========================================================
    # ANOMALY DETECTION
    # ==========================================================

    def detect_anomaly(
        self,
        db: Session,
        device_id: str,
        current_consumption: float,
        period_type: str = "daily",
        limit: int = 30,
    ) -> bool:
        """
        Detect unusually high gas consumption using Z-score.

        Z-score:

            z = (current - mean) / standard_deviation

        Initial business rule:

            z >= 2 → anomaly
            z < 2  → normal
        """

        records = self.get_device_analytics(
            db,
            device_id=device_id,
            period_type=period_type,
            limit=limit,
        )

        historical_values = [
            float(record.consumption_g)
            for record in records
            if record.consumption_g is not None
        ]

        # Not enough history for reliable anomaly detection.
        if len(historical_values) < 3:
            return False

        mean = sum(historical_values) / len(
            historical_values
        )

        variance = sum(
            (value - mean) ** 2
            for value in historical_values
        ) / len(historical_values)

        standard_deviation = variance ** 0.5

        # All historical values are identical.
        if standard_deviation == 0:
            return False

        z_score = (
            current_consumption - mean
        ) / standard_deviation

        return z_score >= 2.0

    # ==========================================================
    # WEIGHTED MOVING AVERAGE FORECAST
    # ==========================================================

    def calculate_weighted_forecast(
        self,
        db: Session,
        device_id: str,
        period_type: str = "daily",
        limit: int = 7,
    ) -> float:
        """
        Predict the next consumption value using a weighted
        moving average.

        Recent consumption gets greater importance.

        Example with 4 records:

            oldest  → 10%
            second  → 20%
            third   → 30%
            newest  → 40%
        """

        records = self.get_device_analytics(
            db,
            device_id=device_id,
            period_type=period_type,
            limit=limit,
        )

        if not records:
            return 0.0

        # Repository returns newest first.
        # Reverse so oldest → newest.
        values = [
            float(record.consumption_g)
            for record in reversed(records)
            if record.consumption_g is not None
        ]

        if not values:
            return 0.0

        # More recent values receive larger weights.
        weights = list(
            range(1, len(values) + 1)
        )

        weighted_sum = sum(
            value * weight
            for value, weight in zip(values, weights)
        )

        total_weight = sum(weights)

        return float(
            weighted_sum / total_weight
        )

    # ==========================================================
    # CREATE CALCULATED ANALYTICS
    # ==========================================================

    def calculate_and_record_usage(
        self,
        db: Session,
        device_id: str,
        start_time: datetime,
        end_time: datetime,
        period_type: str = "daily",
    ) -> UsageAnalytics:
        """
        Complete analytics pipeline:

            Weight readings
                  ↓
            Consumption
                  ↓
            Average rate
                  ↓
            Anomaly detection
                  ↓
            Forecast
                  ↓
            Save UsageAnalytics
        """

        consumption = self.calculate_consumption(
            db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )

        average_rate = self.calculate_average_rate(
            db,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )

        anomaly = self.detect_anomaly(
            db,
            device_id=device_id,
            current_consumption=consumption,
            period_type=period_type,
        )

        forecast = self.calculate_weighted_forecast(
            db,
            device_id=device_id,
            period_type=period_type,
        )

        analytics_data = UsageAnalyticsCreate(
            device_id=device_id,
            period_type=period_type,
            period_start=start_time,
            consumption_g=consumption,
            avg_rate=average_rate,
            anomaly_flag=anomaly,
            forecast_next_g=forecast,
        )

        return self.record_usage(
            db,
            analytics_in=analytics_data
        )

    # ==========================================================
    # ANALYTICS SUMMARY
    # ==========================================================

    def get_summary(
        self,
        db: Session,
        device_id: str,
        period_type: str = "daily"
    ) -> AnalyticsSummary:
        """
        Return an aggregated analytics summary.
        """

        records = self.get_device_analytics(
            db,
            device_id=device_id,
            period_type=period_type
        )

        total = float(
            sum(
                record.consumption_g
                for record in records
            )
        )

        average = (
            total / len(records)
            if records
            else 0.0
        )

        anomaly_count = sum(
            1
            for record in records
            if record.anomaly_flag
        )

        return AnalyticsSummary(
            device_id=device_id,
            period_type=period_type,
            total_consumption_g=total,
            avg_daily_rate_g=average,
            anomaly_count=anomaly_count,
            records=[
                UsageAnalyticsResponse.model_validate(record)
                for record in records
            ],
        )


# ==========================================================
# SERVICE INSTANCE
# ==========================================================

analytics_service = AnalyticsService()