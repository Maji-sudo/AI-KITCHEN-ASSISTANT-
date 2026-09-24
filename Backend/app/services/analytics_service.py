import math
from datetime import datetime, timedelta, timezone, date
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.repositories.analytics_repository import analytics_repo
from app.models.weight_reading import WeightReading
from app.schemas.analytics import (
    DailyConsumptionItem,
    DailyConsumptionResponse,
    WeeklyConsumptionItem,
    WeeklyConsumptionResponse,
    MonthlyConsumptionItem,
    MonthlyConsumptionResponse,
    AverageConsumptionResponse,
    UsagePatternSlot,
    UsagePatternResponse,
    PeakUsageResponse,
    ConsumptionTrendResponse,
    LeakEventItem,
    LeakSummaryResponse,
    EfficiencyScoreResponse,
    AnalyticsSummary,
)


class AnalyticsService:
    """
    Decoupled Analytics Engine for SafeGas AI.

    Computes consumption metrics, usage patterns, peak usage, trends, leak summaries,
    and rule-based efficiency scores directly from PostgreSQL telemetry records.
    """

    # ------------------------------------------------------------------
    # HELPER: CALCULATE CONSECUTIVE DAILY CONSUMPTION DELTAS
    # ------------------------------------------------------------------
    def _compute_daily_deltas(
        self,
        readings: List[WeightReading],
        min_noise_threshold_g: float = 5.0
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculates consecutive weight differences according to strict safety rules:
        1. Sort readings chronologically.
        2. Calculate consecutive weight differences (w1 - w2).
        3. Ignore positive changes (sensor fluctuations or cylinder refills).
        4. Apply min noise threshold (drops < 5g ignored).
        5. Aggregate genuine decreases grouped by local calendar date (YYYY-MM-DD).
        """
        if not readings:
            return {}

        sorted_readings = sorted(readings, key=lambda r: r.timestamp)
        daily_map: Dict[str, Dict[str, Any]] = {}

        max_single_drop = 0.0

        for prev, curr in zip(sorted_readings, sorted_readings[1:]):
            diff = prev.weight_g - curr.weight_g

            # Only genuine decreases exceeding noise threshold
            if diff >= min_noise_threshold_g:
                day_key = curr.timestamp.strftime("%Y-%m-%d")
                if day_key not in daily_map:
                    daily_map[day_key] = {"total_g": 0.0, "count": 0, "drops": []}

                daily_map[day_key]["total_g"] += diff
                daily_map[day_key]["count"] += 1
                daily_map[day_key]["drops"].append((curr.timestamp, diff))

                if diff > max_single_drop:
                    max_single_drop = diff

        return daily_map

    # ------------------------------------------------------------------
    # 1. DAILY CONSUMPTION
    # ------------------------------------------------------------------
    def get_daily_consumption(
        self,
        db: Session,
        device_id: str,
        days: int = 30
    ) -> DailyConsumptionResponse:
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days)

        readings = analytics_repo.get_weight_readings_for_period(
            db, device_id=device_id, start_time=start_time, end_time=now
        )

        daily_map = self._compute_daily_deltas(readings)

        # Build records for each day in date range so days without usage show 0g
        records: List[DailyConsumptionItem] = []
        total_g = 0.0

        for d_offset in range(days):
            day_dt = (start_time + timedelta(days=d_offset)).date()
            day_key = day_dt.strftime("%Y-%m-%d")

            day_data = daily_map.get(day_key, {"total_g": 0.0, "count": 0})
            c_g = round(day_data["total_g"], 2)
            c_kg = round(c_g / 1000.0, 3)
            total_g += c_g

            records.append(
                DailyConsumptionItem(
                    date=day_key,
                    consumption_g=c_g,
                    consumption_kg=c_kg,
                    reading_count=day_data["count"],
                )
            )

        total_kg = round(total_g / 1000.0, 3)
        avg_g = round(total_g / days, 2) if days > 0 else 0.0
        avg_kg = round(avg_g / 1000.0, 3)

        return DailyConsumptionResponse(
            device_id=device_id,
            days=days,
            total_consumption_g=round(total_g, 2),
            total_consumption_kg=total_kg,
            avg_daily_g=avg_g,
            avg_daily_kg=avg_kg,
            records=records,
        )

    # ------------------------------------------------------------------
    # 2. WEEKLY CONSUMPTION
    # ------------------------------------------------------------------
    def get_weekly_consumption(
        self,
        db: Session,
        device_id: str,
        weeks: int = 4
    ) -> WeeklyConsumptionResponse:
        daily_res = self.get_daily_consumption(db, device_id=device_id, days=weeks * 7)

        records: List[WeeklyConsumptionItem] = []
        total_g = 0.0

        for w_idx in range(weeks):
            chunk = daily_res.records[w_idx * 7 : (w_idx + 1) * 7]
            if not chunk:
                continue

            w_total_g = sum(item.consumption_g for item in chunk)
            w_total_kg = round(w_total_g / 1000.0, 3)
            w_avg_g = round(w_total_g / len(chunk), 2)
            total_g += w_total_g

            start_str = chunk[0].date
            end_str = chunk[-1].date
            w_label = f"Week {w_idx + 1} ({start_str} to {end_str})"

            records.append(
                WeeklyConsumptionItem(
                    week_label=w_label,
                    start_date=start_str,
                    end_date=end_str,
                    total_consumption_g=round(w_total_g, 2),
                    total_consumption_kg=w_total_kg,
                    daily_avg_g=w_avg_g,
                    daily_records=chunk,
                )
            )

        total_kg = round(total_g / 1000.0, 3)
        return WeeklyConsumptionResponse(
            device_id=device_id,
            weeks=weeks,
            total_consumption_g=round(total_g, 2),
            total_consumption_kg=total_kg,
            records=records,
        )

    # ------------------------------------------------------------------
    # 3. MONTHLY CONSUMPTION
    # ------------------------------------------------------------------
    def get_monthly_consumption(
        self,
        db: Session,
        device_id: str,
        months: int = 6
    ) -> MonthlyConsumptionResponse:
        daily_res = self.get_daily_consumption(db, device_id=device_id, days=months * 30)

        # Group daily records by YYYY-MM
        monthly_map: Dict[str, List[DailyConsumptionItem]] = {}
        for item in daily_res.records:
            m_key = item.date[:7]  # YYYY-MM
            monthly_map.setdefault(m_key, []).append(item)

        records: List[MonthlyConsumptionItem] = []
        total_g = 0.0

        for m_key in sorted(monthly_map.keys()):
            items = monthly_map[m_key]
            m_total_g = sum(i.consumption_g for i in items)
            m_total_kg = round(m_total_g / 1000.0, 3)
            m_avg_g = round(m_total_g / len(items), 2)
            total_g += m_total_g

            y, m = map(int, m_key.split("-"))
            dt = date(y, m, 1)
            m_label = dt.strftime("%B %Y")

            records.append(
                MonthlyConsumptionItem(
                    month_label=m_label,
                    year=y,
                    month=m,
                    total_consumption_g=round(m_total_g, 2),
                    total_consumption_kg=m_total_kg,
                    daily_avg_g=m_avg_g,
                )
            )

        total_kg = round(total_g / 1000.0, 3)
        return MonthlyConsumptionResponse(
            device_id=device_id,
            months=months,
            total_consumption_g=round(total_g, 2),
            total_consumption_kg=total_kg,
            records=records,
        )

    # ------------------------------------------------------------------
    # 4. AVERAGE CONSUMPTION
    # ------------------------------------------------------------------
    def get_average_consumption(
        self,
        db: Session,
        device_id: str,
        days: int = 30
    ) -> AverageConsumptionResponse:
        daily_res = self.get_daily_consumption(db, device_id=device_id, days=days)

        active_days = [item for item in daily_res.records if item.consumption_g > 0]
        analyzed_days = len(daily_res.records) if daily_res.records else 1

        total_g = daily_res.total_consumption_g
        avg_daily_g = round(total_g / analyzed_days, 2)
        avg_daily_kg = round(avg_daily_g / 1000.0, 3)

        avg_weekly_g = round(avg_daily_g * 7, 2)
        avg_weekly_kg = round(avg_weekly_g / 1000.0, 3)

        return AverageConsumptionResponse(
            device_id=device_id,
            avg_daily_g=avg_daily_g,
            avg_daily_kg=avg_daily_kg,
            avg_weekly_g=avg_weekly_g,
            avg_weekly_kg=avg_weekly_kg,
            total_days_analyzed=analyzed_days,
        )

    # ------------------------------------------------------------------
    # 5. USAGE PATTERN BY TIME-OF-DAY
    # ------------------------------------------------------------------
    def get_usage_pattern(
        self,
        db: Session,
        device_id: str,
        days: int = 30
    ) -> UsagePatternResponse:
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days)

        readings = analytics_repo.get_weight_readings_for_period(
            db, device_id=device_id, start_time=start_time, end_time=now
        )
        sorted_readings = sorted(readings, key=lambda r: r.timestamp)

        slots_data = {
            "Morning": {"range": "05:00 - 11:59", "total_g": 0.0, "count": 0},
            "Afternoon": {"range": "12:00 - 16:59", "total_g": 0.0, "count": 0},
            "Evening": {"range": "17:00 - 21:59", "total_g": 0.0, "count": 0},
            "Night": {"range": "22:00 - 04:59", "total_g": 0.0, "count": 0},
        }

        total_g = 0.0

        for prev, curr in zip(sorted_readings, sorted_readings[1:]):
            diff = prev.weight_g - curr.weight_g
            if diff >= 5.0:
                hour = curr.timestamp.hour
                if 5 <= hour < 12:
                    slot_name = "Morning"
                elif 12 <= hour < 17:
                    slot_name = "Afternoon"
                elif 17 <= hour < 22:
                    slot_name = "Evening"
                else:
                    slot_name = "Night"

                slots_data[slot_name]["total_g"] += diff
                slots_data[slot_name]["count"] += 1
                total_g += diff

        slots_list: List[UsagePatternSlot] = []
        peak_period = "Morning"
        max_slot_g = -1.0

        for s_name, s_info in slots_data.items():
            g_val = round(s_info["total_g"], 2)
            pct = round((g_val / total_g * 100.0), 1) if total_g > 0 else 0.0

            if g_val > max_slot_g:
                max_slot_g = g_val
                peak_period = s_name

            slots_list.append(
                UsagePatternSlot(
                    slot_name=s_name,
                    time_range=s_info["range"],
                    consumption_g=g_val,
                    consumption_kg=round(g_val / 1000.0, 3),
                    percentage=pct,
                    drop_events_count=s_info["count"],
                )
            )

        return UsagePatternResponse(
            device_id=device_id,
            peak_period=peak_period,
            slots=slots_list,
            total_consumption_g=round(total_g, 2),
        )

    # ------------------------------------------------------------------
    # 6. PEAK USAGE
    # ------------------------------------------------------------------
    def get_peak_usage(
        self,
        db: Session,
        device_id: str,
        days: int = 30
    ) -> PeakUsageResponse:
        daily_res = self.get_daily_consumption(db, device_id=device_id, days=days)
        pattern_res = self.get_usage_pattern(db, device_id=device_id, days=days)

        highest_item = None
        max_day_g = -1.0

        for item in daily_res.records:
            if item.consumption_g > max_day_g:
                max_day_g = item.consumption_g
                highest_item = item

        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days)
        readings = analytics_repo.get_weight_readings_for_period(
            db, device_id=device_id, start_time=start_time, end_time=now
        )
        sorted_readings = sorted(readings, key=lambda r: r.timestamp)

        max_single_drop = 0.0
        for prev, curr in zip(sorted_readings, sorted_readings[1:]):
            diff = prev.weight_g - curr.weight_g
            if diff > max_single_drop:
                max_single_drop = diff

        return PeakUsageResponse(
            device_id=device_id,
            highest_day_date=highest_item.date if highest_item else None,
            highest_day_consumption_g=round(max_day_g if highest_item else 0.0, 2),
            highest_day_consumption_kg=round((max_day_g / 1000.0) if highest_item else 0.0, 3),
            peak_period=pattern_res.peak_period,
            max_single_drop_g=round(max_single_drop, 2),
        )

    # ------------------------------------------------------------------
    # 7. CONSUMPTION TREND
    # ------------------------------------------------------------------
    def get_consumption_trend(
        self,
        db: Session,
        device_id: str,
        period_days: int = 7
    ) -> ConsumptionTrendResponse:
        recent_daily = self.get_daily_consumption(db, device_id=device_id, days=period_days)
        prior_res = self.get_daily_consumption(db, device_id=device_id, days=period_days * 2)

        prior_chunk = prior_res.records[:period_days]
        prior_total = sum(i.consumption_g for i in prior_chunk)
        prior_avg = round(prior_total / len(prior_chunk), 2) if prior_chunk else 0.0

        recent_avg = recent_daily.avg_daily_g

        if prior_avg <= 0:
            trend = "stable"
            pct_change = 0.0
            desc = "Consumption is stable with baseline data gathering."
        else:
            pct_change = round(((recent_avg - prior_avg) / prior_avg) * 100.0, 1)
            if pct_change > 5.0:
                trend = "increasing"
                desc = f"Consumption increased by {pct_change}% compared to the prior {period_days}-day period."
            elif pct_change < -5.0:
                trend = "decreasing"
                desc = f"Consumption decreased by {abs(pct_change)}% compared to the prior {period_days}-day period."
            else:
                trend = "stable"
                desc = f"Consumption remains steady ({pct_change}% shift) compared to prior period."

        return ConsumptionTrendResponse(
            device_id=device_id,
            trend=trend,
            percent_change=pct_change,
            recent_period_avg_g=recent_avg,
            prior_period_avg_g=prior_avg,
            description=desc,
        )

    # ------------------------------------------------------------------
    # 8. LEAK EVENTS SUMMARY
    # ------------------------------------------------------------------
    def get_leak_summary(
        self,
        db: Session,
        device_id: str,
        days: int = 30
    ) -> LeakSummaryResponse:
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days)

        events = analytics_repo.get_leak_events_for_period(
            db, device_id=device_id, start_time=start_time, end_time=now
        )
        gas_readings = analytics_repo.get_gas_readings_for_period(
            db, device_id=device_id, start_time=start_time, end_time=now
        )

        peak_ppm = max([r.ppm_value for r in gas_readings], default=0.0)
        auto_shutoffs = sum(1 for e in events if e.auto_shutoff_triggered)

        recent_items = [
            LeakEventItem(
                id=e.id,
                start_time=e.start_time,
                end_time=e.end_time,
                peak_ppm=e.peak_ppm,
                auto_shutoff_triggered=e.auto_shutoff_triggered,
                false_alarm=e.false_alarm,
            )
            for e in events[:5]
        ]

        return LeakSummaryResponse(
            device_id=device_id,
            total_leaks=len(events),
            auto_shutoffs_triggered=auto_shutoffs,
            peak_ppm=round(peak_ppm, 1),
            recent_events=recent_items,
        )

    # ------------------------------------------------------------------
    # 9. RULE-BASED TRANSPARENT EFFICIENCY SCORE (0–100)
    # ------------------------------------------------------------------
    def get_efficiency_score(
        self,
        db: Session,
        device_id: str,
        days: int = 30
    ) -> EfficiencyScoreResponse:
        """
        Transparent, deterministic rule-based efficiency score (0–100):

        Formula:
            Base Score = 100

            Deduction Rules:
            1. Safety / Leak Events: -15 per leak event (max -40)
            2. Gas Warning Spike: -10 if max PPM > 400
            3. Night Usage Penalty: -10 if Night usage (22:00-05:00) > 15% of total
            4. Volatility Penalty: -15 if StdDev of daily consumption > 1.5 * Mean

            Final Score = clamp(Base - Deductions, 0, 100)
        """
        daily_res = self.get_daily_consumption(db, device_id=device_id, days=days)
        pattern_res = self.get_usage_pattern(db, device_id=device_id, days=days)
        leak_res = self.get_leak_summary(db, device_id=device_id, days=days)

        base_score = 100.0
        deductions = []

        # Rule 1: Leak Events Penalty
        leak_penalty = min(40.0, leak_res.total_leaks * 15.0)
        if leak_penalty > 0:
            deductions.append(f"-{leak_penalty:.0f} pts for {leak_res.total_leaks} leak event(s)")

        # Rule 2: High Gas PPM Warning Penalty
        gas_ppm_penalty = 0.0
        if leak_res.peak_ppm > 400.0:
            gas_ppm_penalty = 10.0
            deductions.append(f"-10 pts for elevated gas concentration ({leak_res.peak_ppm:.0f} PPM peak)")

        # Rule 3: Night / Idle Usage Penalty
        night_penalty = 0.0
        night_slot = next((s for s in pattern_res.slots if s.slot_name == "Night"), None)
        if night_slot and night_slot.percentage > 15.0:
            night_penalty = 10.0
            deductions.append(f"-10 pts for high night-time usage ({night_slot.percentage}% of total)")

        # Rule 4: Consumption Volatility Penalty
        volatility_penalty = 0.0
        vals = [d.consumption_g for d in daily_res.records if d.consumption_g > 0]
        if len(vals) >= 3:
            mean = sum(vals) / len(vals)
            variance = sum((x - mean) ** 2 for x in vals) / len(vals)
            std_dev = math.sqrt(variance)
            if std_dev > (1.5 * mean) and mean > 0:
                volatility_penalty = 15.0
                deductions.append(f"-15 pts for highly erratic daily consumption spikes")

        total_deduction = leak_penalty + gas_ppm_penalty + night_penalty + volatility_penalty
        overall_score = max(0.0, min(100.0, base_score - total_deduction))

        if overall_score >= 90.0:
            grade = "A"
        elif overall_score >= 80.0:
            grade = "B"
        elif overall_score >= 70.0:
            grade = "C"
        else:
            grade = "D"

        explanation = (
            f"Overall kitchen safety & efficiency score is {overall_score:.0f}/100 (Grade {grade}). "
            + ("Deductions: " + ", ".join(deductions) if deductions else "No penalties applied — optimal kitchen efficiency!")
        )

        components_json = {
            "safety_score": round(100.0 - leak_penalty - gas_ppm_penalty, 1),
            "consumption_consistency": round(100.0 - volatility_penalty, 1),
            "idle_usage_efficiency": round(100.0 - night_penalty, 1),
            "leak_events_count": leak_res.total_leaks,
            "peak_ppm": leak_res.peak_ppm,
            "night_usage_percentage": night_slot.percentage if night_slot else 0.0,
            "deductions": deductions,
        }

        return EfficiencyScoreResponse(
            device_id=device_id,
            overall_score=round(overall_score, 1),
            grade=grade,
            explanation=explanation,
            components_json=components_json,
        )

    # ------------------------------------------------------------------
    # 10. FULL SUMMARY
    # ------------------------------------------------------------------
    def get_full_summary(
        self,
        db: Session,
        device_id: str,
        days: int = 30
    ) -> AnalyticsSummary:
        daily_res = self.get_daily_consumption(db, device_id=device_id, days=days)
        averages_res = self.get_average_consumption(db, device_id=device_id, days=days)
        pattern_res = self.get_usage_pattern(db, device_id=device_id, days=days)
        peak_res = self.get_peak_usage(db, device_id=device_id, days=days)
        trend_res = self.get_consumption_trend(db, device_id=device_id, period_days=min(7, days))
        leak_res = self.get_leak_summary(db, device_id=device_id, days=days)
        eff_res = self.get_efficiency_score(db, device_id=device_id, days=days)

        return AnalyticsSummary(
            device_id=device_id,
            period_days=days,
            daily=daily_res,
            averages=averages_res,
            usage_pattern=pattern_res,
            peak_usage=peak_res,
            trend=trend_res,
            leak_summary=leak_res,
            efficiency=eff_res,
        )


analytics_service = AnalyticsService()