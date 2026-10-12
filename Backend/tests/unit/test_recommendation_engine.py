"""
Unit tests for each recommendation rule in isolation.
All rules are tested via the RecommendationEngine.evaluate() method
with minimal synthetic AnalyticsSummary / CookingHistory objects.
"""
import math
import pytest
from unittest.mock import MagicMock

from app.services.recommendation_engine import RecommendationEngine, RuleOutput
from app.schemas.analytics import (
    AnalyticsSummary,
    DailyConsumptionResponse,
    DailyConsumptionItem,
    AverageConsumptionResponse,
    UsagePatternResponse,
    UsagePatternSlot,
    PeakUsageResponse,
    ConsumptionTrendResponse,
    LeakSummaryResponse,
    EfficiencyScoreResponse,
)

engine = RecommendationEngine()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_summary(
    *,
    total_leaks: int = 0,
    auto_shutoffs: int = 0,
    peak_ppm: float = 0.0,
    trend: str = "stable",
    percent_change: float = 0.0,
    recent_avg_g: float = 300.0,
    prior_avg_g: float = 300.0,
    night_pct: float = 5.0,
    total_consumption_g: float = 9000.0,
    grade: str = "B",
    overall_score: float = 85.0,
    deductions: list = None,
    avg_daily_g: float = 300.0,
    total_days_analyzed: int = 30,
    daily_records: list = None,
    device_id: str = "SGD-TEST-001",
    period_days: int = 30,
) -> AnalyticsSummary:
    """Build a minimal AnalyticsSummary for unit-testing individual rules."""
    if daily_records is None:
        daily_records = [
            DailyConsumptionItem(
                date=f"2026-09-{i+1:02d}",
                consumption_g=avg_daily_g if i % 3 != 0 else 0.0,
                consumption_kg=avg_daily_g / 1000,
                reading_count=1,
            )
            for i in range(30)
        ]

    return AnalyticsSummary(
        device_id=device_id,
        period_days=period_days,
        daily=DailyConsumptionResponse(
            device_id=device_id,
            days=period_days,
            total_consumption_g=total_consumption_g,
            total_consumption_kg=total_consumption_g / 1000,
            avg_daily_g=avg_daily_g,
            avg_daily_kg=avg_daily_g / 1000,
            records=daily_records,
        ),
        averages=AverageConsumptionResponse(
            device_id=device_id,
            avg_daily_g=avg_daily_g,
            avg_daily_kg=avg_daily_g / 1000,
            avg_weekly_g=avg_daily_g * 7,
            avg_weekly_kg=avg_daily_g * 7 / 1000,
            total_days_analyzed=total_days_analyzed,
        ),
        usage_pattern=UsagePatternResponse(
            device_id=device_id,
            peak_period="Morning",
            total_consumption_g=total_consumption_g,
            slots=[
                UsagePatternSlot(
                    slot_name="Morning",
                    time_range="05:00 - 11:59",
                    consumption_g=total_consumption_g * 0.5,
                    consumption_kg=total_consumption_g * 0.5 / 1000,
                    percentage=50.0,
                    drop_events_count=10,
                ),
                UsagePatternSlot(
                    slot_name="Afternoon",
                    time_range="12:00 - 16:59",
                    consumption_g=total_consumption_g * 0.3,
                    consumption_kg=total_consumption_g * 0.3 / 1000,
                    percentage=30.0,
                    drop_events_count=6,
                ),
                UsagePatternSlot(
                    slot_name="Evening",
                    time_range="17:00 - 21:59",
                    consumption_g=total_consumption_g * (1 - 0.5 - 0.3 - night_pct / 100),
                    consumption_kg=0.0,
                    percentage=20.0 - night_pct,
                    drop_events_count=4,
                ),
                UsagePatternSlot(
                    slot_name="Night",
                    time_range="22:00 - 04:59",
                    consumption_g=total_consumption_g * night_pct / 100,
                    consumption_kg=total_consumption_g * night_pct / 100 / 1000,
                    percentage=night_pct,
                    drop_events_count=2,
                ),
            ],
        ),
        peak_usage=PeakUsageResponse(
            device_id=device_id,
            peak_period="Morning",
        ),
        trend=ConsumptionTrendResponse(
            device_id=device_id,
            trend=trend,
            percent_change=percent_change,
            recent_period_avg_g=recent_avg_g,
            prior_period_avg_g=prior_avg_g,
            description="test",
        ),
        leak_summary=LeakSummaryResponse(
            device_id=device_id,
            total_leaks=total_leaks,
            auto_shutoffs_triggered=auto_shutoffs,
            peak_ppm=peak_ppm,
        ),
        efficiency=EfficiencyScoreResponse(
            device_id=device_id,
            overall_score=overall_score,
            grade=grade,
            explanation="test",
            components_json={"deductions": deductions or []},
        ),
    )


def _make_session(actual_g: float, base_g: float, dish_name: str = "Dal") -> MagicMock:
    """Return a mock CookingHistory session with a linked Dish."""
    dish = MagicMock()
    dish.id = 1
    dish.dish_name = dish_name
    dish.base_gas_g = base_g
    session = MagicMock()
    session.actual_gas_g = actual_g
    session.dish = dish
    return session


def _make_refill(days_left: int, confidence: float = 0.90) -> MagicMock:
    from datetime import datetime, timezone, timedelta
    pred = MagicMock()
    pred.days_left = days_left
    pred.confidence = confidence
    pred.predicted_empty_date = datetime.now(timezone.utc) + timedelta(days=days_left)
    return pred


# ── R01 — Leak events ─────────────────────────────────────────────────────────

class TestR01:
    def test_fires_when_leaks_present(self):
        s = _build_summary(total_leaks=2, auto_shutoffs=1, peak_ppm=350.0)
        results = engine._r01_leak_events(s)
        assert len(results) == 1
        r = results[0]
        assert r.rule_id == "R01"
        assert r.category == "safety"
        assert r.priority == 1
        assert "2" in r.message
        assert "auto-shutoff" in r.message.lower()
        assert r.supporting_facts["total_leaks"] == 2

    def test_fires_with_no_shutoffs(self):
        s = _build_summary(total_leaks=1, auto_shutoffs=0)
        results = engine._r01_leak_events(s)
        assert len(results) == 1
        assert "No auto-shutoffs" in results[0].message

    def test_skips_when_zero_leaks(self):
        s = _build_summary(total_leaks=0)
        assert engine._r01_leak_events(s) == []

    def test_message_does_not_claim_current_leak(self):
        """R01 must never say gas is currently leaking."""
        s = _build_summary(total_leaks=3, peak_ppm=1500.0)
        msg = engine._r01_leak_events(s)[0].message.lower()
        assert "currently" not in msg
        assert "active leak" not in msg


# ── R02 — High PPM ────────────────────────────────────────────────────────────

class TestR02:
    def test_fires_above_threshold(self):
        s = _build_summary(peak_ppm=800.0)
        results = engine._r02_high_ppm(s)
        assert len(results) == 1
        assert results[0].rule_id == "R02"
        assert "800" in results[0].message

    def test_fires_critically_above_1000(self):
        s = _build_summary(peak_ppm=1200.0)
        msg = engine._r02_high_ppm(s)[0].message.lower()
        assert "critically high" in msg

    def test_skips_at_or_below_threshold(self):
        s = _build_summary(peak_ppm=400.0)
        assert engine._r02_high_ppm(s) == []

    def test_skips_zero_ppm(self):
        s = _build_summary(peak_ppm=0.0)
        assert engine._r02_high_ppm(s) == []

    def test_message_says_historical_reading(self):
        """R02 must be explicit that the reading is historical."""
        s = _build_summary(peak_ppm=600.0)
        msg = engine._r02_high_ppm(s)[0].message.lower()
        assert "historical" in msg or "recorded" in msg


# ── R03 — Rising trend ────────────────────────────────────────────────────────

class TestR03:
    def test_fires_when_trend_increasing_above_threshold(self):
        s = _build_summary(trend="increasing", percent_change=20.0,
                           recent_avg_g=360.0, prior_avg_g=300.0)
        results = engine._r03_rising_trend(s)
        assert len(results) == 1
        assert results[0].rule_id == "R03"
        assert "20.0%" in results[0].message

    def test_skips_when_trend_stable(self):
        s = _build_summary(trend="stable", percent_change=3.0,
                           recent_avg_g=310.0, prior_avg_g=300.0)
        assert engine._r03_rising_trend(s) == []

    def test_skips_when_trend_decreasing(self):
        s = _build_summary(trend="decreasing", percent_change=-10.0,
                           recent_avg_g=270.0, prior_avg_g=300.0)
        assert engine._r03_rising_trend(s) == []

    def test_skips_increasing_but_below_threshold(self):
        s = _build_summary(trend="increasing", percent_change=10.0,
                           recent_avg_g=330.0, prior_avg_g=300.0)
        assert engine._r03_rising_trend(s) == []

    def test_skips_when_no_prior_baseline(self):
        """If prior_avg_g is 0 there is no baseline — must not fire."""
        s = _build_summary(trend="increasing", percent_change=50.0,
                           recent_avg_g=300.0, prior_avg_g=0.0)
        assert engine._r03_rising_trend(s) == []


# ── R04 — Night usage ─────────────────────────────────────────────────────────

class TestR04:
    def test_fires_when_night_pct_above_threshold(self):
        s = _build_summary(night_pct=20.0, total_consumption_g=9000.0)
        results = engine._r04_night_usage(s)
        assert len(results) == 1
        assert results[0].rule_id == "R04"
        assert "20.0%" in results[0].message

    def test_skips_when_night_pct_at_threshold(self):
        s = _build_summary(night_pct=15.0, total_consumption_g=9000.0)
        assert engine._r04_night_usage(s) == []

    def test_skips_when_no_total_consumption(self):
        s = _build_summary(night_pct=20.0, total_consumption_g=0.0)
        assert engine._r04_night_usage(s) == []

    def test_supporting_facts_include_night_consumption(self):
        s = _build_summary(night_pct=25.0, total_consumption_g=10000.0)
        facts = engine._r04_night_usage(s)[0].supporting_facts
        assert "night_usage_pct" in facts
        assert facts["night_usage_pct"] == 25.0


# ── R05 — Low efficiency grade ────────────────────────────────────────────────

class TestR05:
    def test_fires_for_grade_c(self):
        s = _build_summary(grade="C", overall_score=72.0,
                           deductions=["leak penalty"])
        results = engine._r05_low_efficiency_grade(s)
        assert len(results) == 1
        assert results[0].rule_id == "R05"
        assert "Grade C" in results[0].message

    def test_fires_for_grade_d(self):
        s = _build_summary(grade="D", overall_score=55.0,
                           deductions=["-15 pts for erratic usage"])
        results = engine._r05_low_efficiency_grade(s)
        assert len(results) == 1

    def test_skips_for_grade_a(self):
        s = _build_summary(grade="A", overall_score=95.0)
        assert engine._r05_low_efficiency_grade(s) == []

    def test_skips_for_grade_b(self):
        s = _build_summary(grade="B", overall_score=82.0)
        assert engine._r05_low_efficiency_grade(s) == []

    def test_confidence_higher_for_worse_grade(self):
        s_c = _build_summary(grade="C", overall_score=72.0)
        s_d = _build_summary(grade="D", overall_score=50.0)
        conf_c = engine._r05_low_efficiency_grade(s_c)[0].confidence
        conf_d = engine._r05_low_efficiency_grade(s_d)[0].confidence
        assert conf_d > conf_c


# ── R06 — Heavy daily use ─────────────────────────────────────────────────────

class TestR06:
    def test_fires_above_threshold_with_enough_days(self):
        s = _build_summary(avg_daily_g=700.0, total_days_analyzed=10)
        results = engine._r06_heavy_daily_use(s)
        assert len(results) == 1
        assert "700" in results[0].message

    def test_skips_below_threshold(self):
        s = _build_summary(avg_daily_g=500.0, total_days_analyzed=10)
        assert engine._r06_heavy_daily_use(s) == []

    def test_skips_insufficient_days(self):
        """Must require at least 3 days before firing."""
        s = _build_summary(avg_daily_g=800.0, total_days_analyzed=2)
        assert engine._r06_heavy_daily_use(s) == []

    def test_supporting_facts_include_threshold(self):
        s = _build_summary(avg_daily_g=650.0, total_days_analyzed=5)
        facts = engine._r06_heavy_daily_use(s)[0].supporting_facts
        assert facts["threshold_g"] == 600.0


# ── R07 — Dish over-consumption ───────────────────────────────────────────────

class TestR07:
    def test_fires_when_actual_exceeds_base(self):
        sessions = [_make_session(actual_g=150.0, base_g=80.0, dish_name="Dal")]
        results = engine._r07_overconsumption_vs_dish(sessions)
        assert len(results) == 1
        r = results[0]
        assert r.rule_id == "R07"
        assert "Dal" in r.message
        assert r.supporting_facts["baseline_gas_g"] == 80.0
        assert r.supporting_facts["actual_gas_g"] == 150.0

    def test_skips_when_actual_within_factor(self):
        sessions = [_make_session(actual_g=100.0, base_g=80.0)]
        assert engine._r07_overconsumption_vs_dish(sessions) == []

    def test_skips_when_no_dish_linked(self):
        session = MagicMock()
        session.actual_gas_g = 200.0
        session.dish = None
        assert engine._r07_overconsumption_vs_dish([session]) == []

    def test_skips_when_actual_gas_is_none(self):
        session = MagicMock()
        session.actual_gas_g = None
        dish = MagicMock()
        dish.id = 1
        dish.dish_name = "Rice"
        dish.base_gas_g = 50.0
        session.dish = dish
        assert engine._r07_overconsumption_vs_dish([session]) == []

    def test_skips_when_base_gas_is_zero(self):
        sessions = [_make_session(actual_g=100.0, base_g=0.0)]
        assert engine._r07_overconsumption_vs_dish(sessions) == []

    def test_caps_at_two_dish_outputs(self):
        sessions = [
            _make_session(actual_g=200.0, base_g=80.0, dish_name=f"Dish{i}")
            for i in range(5)
        ]
        # Give each dish a unique id
        for i, s in enumerate(sessions):
            s.dish.id = i
        results = engine._r07_overconsumption_vs_dish(sessions)
        assert len(results) == 2

    def test_flags_each_dish_only_once(self):
        dish = MagicMock()
        dish.id = 42
        dish.dish_name = "Biryani"
        dish.base_gas_g = 80.0
        sessions = []
        for _ in range(3):
            s = MagicMock()
            s.actual_gas_g = 200.0
            s.dish = dish
            sessions.append(s)
        results = engine._r07_overconsumption_vs_dish(sessions)
        assert len(results) == 1

    def test_empty_history_returns_empty(self):
        assert engine._r07_overconsumption_vs_dish([]) == []


# ── R08 — Infrequent cooking ──────────────────────────────────────────────────

class TestR08:
    def test_fires_when_below_minimum(self):
        sessions = [MagicMock() for _ in range(2)]
        results = engine._r08_infrequent_cooking(sessions)
        assert len(results) == 1
        assert results[0].rule_id == "R08"
        assert "2" in results[0].message

    def test_skips_when_at_minimum(self):
        sessions = [MagicMock() for _ in range(3)]
        assert engine._r08_infrequent_cooking(sessions) == []

    def test_skips_when_above_minimum(self):
        sessions = [MagicMock() for _ in range(10)]
        assert engine._r08_infrequent_cooking(sessions) == []

    def test_fires_when_zero_sessions(self):
        assert len(engine._r08_infrequent_cooking([])) == 1


# ── R09 — Refill soon ─────────────────────────────────────────────────────────

class TestR09:
    def test_fires_when_prediction_below_threshold(self):
        pred = _make_refill(days_left=5, confidence=0.90)
        results = engine._r09_refill_soon(pred)
        assert len(results) == 1
        r = results[0]
        assert r.rule_id == "R09"
        assert "5" in r.message
        assert r.confidence <= 0.95

    def test_skips_when_days_left_above_threshold(self):
        pred = _make_refill(days_left=10, confidence=0.90)
        assert engine._r09_refill_soon(pred) == []

    def test_skips_when_no_prediction(self):
        """Must skip entirely if no prediction exists — no heuristics."""
        assert engine._r09_refill_soon(None) == []

    def test_confidence_capped_at_095(self):
        pred = _make_refill(days_left=1, confidence=0.99)
        r = engine._r09_refill_soon(pred)[0]
        assert r.confidence <= 0.95


# ── R10 — Consumption volatility ─────────────────────────────────────────────

class TestR10:
    def _make_volatile_records(self, n: int = 10) -> list:
        """
        8 days at 10g + 2 days at 3000g:
          mean = (8*10 + 2*3000) / 10 = 6080/10 = 608
          variance = (8*(10-608)^2 + 2*(3000-608)^2) / 10
                   = (8*357604 + 2*5722864) / 10
                   = (2860832 + 11445728) / 10 = 1430656
          std_dev ≈ 1196
          1.5 * mean = 912   →   1196 > 912  ✓  R10 fires
        """
        items = []
        for i in range(n):
            val = 10.0 if i < 8 else 3000.0
            items.append(DailyConsumptionItem(
                date=f"2026-09-{i+1:02d}",
                consumption_g=val,
                consumption_kg=val / 1000,
                reading_count=1,
            ))
        return items

    def _make_steady_records(self, n: int = 10, val: float = 300.0) -> list:
        return [
            DailyConsumptionItem(
                date=f"2026-09-{i+1:02d}",
                consumption_g=val,
                consumption_kg=val / 1000,
                reading_count=1,
            )
            for i in range(n)
        ]

    def test_fires_for_volatile_consumption(self):
        s = _build_summary(daily_records=self._make_volatile_records())
        results = engine._r10_consumption_volatility(s)
        assert len(results) == 1
        assert results[0].rule_id == "R10"

    def test_skips_for_steady_consumption(self):
        s = _build_summary(daily_records=self._make_steady_records(10, 300.0))
        assert engine._r10_consumption_volatility(s) == []

    def test_skips_when_fewer_than_minimum_days(self):
        s = _build_summary(daily_records=self._make_volatile_records(n=4))
        assert engine._r10_consumption_volatility(s) == []

    def test_skips_when_all_zero(self):
        s = _build_summary(daily_records=self._make_steady_records(10, 0.0))
        assert engine._r10_consumption_volatility(s) == []

    def test_cv_in_supporting_facts(self):
        s = _build_summary(daily_records=self._make_volatile_records(10))
        results = engine._r10_consumption_volatility(s)
        assert len(results) == 1, "R10 should fire with these volatile values"
        facts = results[0].supporting_facts
        assert "coefficient_of_variation_pct" in facts
        assert facts["coefficient_of_variation_pct"] > 0


# ── Evaluate() — integration across all rules ─────────────────────────────────

class TestEvaluate:
    def test_returns_empty_when_nothing_fires(self):
        s = _build_summary(
            total_leaks=0, peak_ppm=0.0,
            trend="stable", percent_change=0.0,
            night_pct=5.0, grade="A", overall_score=95.0,
            avg_daily_g=200.0, total_days_analyzed=30,
        )
        results = engine.evaluate(s, [], None)
        # R08 will fire because we pass empty history — that's expected
        rule_ids = [r.rule_id for r in results]
        assert "R01" not in rule_ids
        assert "R02" not in rule_ids
        assert "R03" not in rule_ids
        assert "R08" in rule_ids  # 0 sessions triggers R08

    def test_sorted_by_priority(self):
        s = _build_summary(
            total_leaks=1,   # R01 priority=1
            peak_ppm=600.0,  # R02 priority=1
            trend="increasing", percent_change=25.0,
            recent_avg_g=375.0, prior_avg_g=300.0,  # R03 priority=2
            night_pct=20.0,  # R04 priority=2
            avg_daily_g=700.0, total_days_analyzed=10,  # R06 priority=3
        )
        results = engine.evaluate(s, [], None)
        priorities = [r.priority for r in results]
        assert priorities == sorted(priorities)

    def test_bad_rule_does_not_abort_others(self):
        """If one rule raises, the rest should still evaluate."""
        s = _build_summary(total_leaks=1, peak_ppm=600.0)

        original = engine._r03_rising_trend
        engine._r03_rising_trend = lambda x: 1 / 0  # force ZeroDivisionError
        try:
            results = engine.evaluate(s, [], None)
            rule_ids = [r.rule_id for r in results]
            assert "R01" in rule_ids
            assert "R02" in rule_ids
            assert "R03" not in rule_ids
        finally:
            engine._r03_rising_trend = original
