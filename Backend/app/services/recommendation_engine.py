"""
SafeGas AI — Deterministic Rule-Based Recommendation Engine (v1)
================================================================
No external AI APIs, no ML inference, no invented benchmarks.
Produces typed RuleOutput objects from existing analytics summary,
cooking history, and refill prediction data already in the DB.

Rules handle missing / insufficient data safely — they return [] when
the data needed to evaluate the rule is absent or below the minimum
required to be meaningful.

Rule catalogue
--------------
ID   Category    Trigger condition
---- ----------- -----------------------------------------------------------
R01  safety      ≥1 confirmed leak event in analysis window
R02  safety      Peak gas PPM > 400 (historical reading — NOT a live alert)
R03  efficiency  Consumption trend increasing > 15 % vs prior period
R04  efficiency  Night-time usage (22:00–05:00) > 15 % of total
R05  efficiency  Efficiency grade is C or D
R06  efficiency  Average daily consumption > 600 g
R07  cooking     Any dish: actual_gas_g > 1.5× its stored base_gas_g
R08  cooking     Fewer than MIN_COOKING_SESSIONS logged in window
R09  refill      Existing RefillPrediction.days_left ≤ REFILL_DAYS_LEFT
R10  efficiency  High consumption volatility: daily std-dev > 1.5× mean
"""

from __future__ import annotations

import math
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.schemas.analytics import AnalyticsSummary
from app.models.cooking_history import CookingHistory
from app.models.refill_prediction import RefillPrediction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data transfer object — one recommendation produced by a rule
# ---------------------------------------------------------------------------

@dataclass
class RuleOutput:
    rule_id: str
    category: str          # safety | efficiency | cooking | refill | general
    priority: int          # 1=critical | 2=high | 3=medium | 4=low
    message: str
    confidence: float      # 0.0 – 1.0
    supporting_facts: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class RecommendationEngine:
    """
    Stateless, deterministic recommendation engine.

    Call `evaluate(summary, cooking_history, latest_refill_prediction)` to
    receive a priority-sorted list of RuleOutput objects.
    Each call is independent; persistence is the caller's responsibility.
    """

    # ── Thresholds (tune here without touching rule logic) ─────────────────
    LEAK_TRIGGER_COUNT: int = 1
    HIGH_PPM_THRESHOLD: float = 400.0
    TREND_INCREASE_PCT: float = 15.0
    NIGHT_USAGE_PCT: float = 15.0
    LOW_EFFICIENCY_GRADES = frozenset({"C", "D"})
    HEAVY_USE_G_PER_DAY: float = 600.0
    OVERCONSUMPTION_FACTOR: float = 1.5
    MIN_COOKING_SESSIONS: int = 3
    MIN_ACTIVE_DAYS_FOR_VOLATILITY: int = 5   # minimum active days needed to run R10
    VOLATILITY_FACTOR: float = 1.5            # std_dev must exceed FACTOR × mean to fire R10
    REFILL_DAYS_LEFT: int = 7

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def evaluate(
        self,
        summary: AnalyticsSummary,
        cooking_history: List[CookingHistory],
        latest_refill_prediction: Optional[RefillPrediction] = None,
    ) -> List[RuleOutput]:
        """
        Run all rules. Returns a deduplicated, priority-sorted list.
        Each rule returns [] when data is missing/insufficient.
        """
        outputs: List[RuleOutput] = []

        try:
            outputs.extend(self._r01_leak_events(summary))
        except Exception:
            logger.exception("R01 failed — skipping")

        try:
            outputs.extend(self._r02_high_ppm(summary))
        except Exception:
            logger.exception("R02 failed — skipping")

        try:
            outputs.extend(self._r03_rising_trend(summary))
        except Exception:
            logger.exception("R03 failed — skipping")

        try:
            outputs.extend(self._r04_night_usage(summary))
        except Exception:
            logger.exception("R04 failed — skipping")

        try:
            outputs.extend(self._r05_low_efficiency_grade(summary))
        except Exception:
            logger.exception("R05 failed — skipping")

        try:
            outputs.extend(self._r06_heavy_daily_use(summary))
        except Exception:
            logger.exception("R06 failed — skipping")

        try:
            outputs.extend(self._r07_overconsumption_vs_dish(cooking_history))
        except Exception:
            logger.exception("R07 failed — skipping")

        try:
            outputs.extend(self._r08_infrequent_cooking(cooking_history))
        except Exception:
            logger.exception("R08 failed — skipping")

        try:
            outputs.extend(self._r09_refill_soon(latest_refill_prediction))
        except Exception:
            logger.exception("R09 failed — skipping")

        try:
            outputs.extend(self._r10_consumption_volatility(summary))
        except Exception:
            logger.exception("R10 failed — skipping")

        outputs.sort(key=lambda o: o.priority)

        logger.info(
            "RecommendationEngine: %d rule(s) fired for device_id=%s",
            len(outputs),
            summary.device_id,
        )
        return outputs

    # ------------------------------------------------------------------
    # R01 — Leak events detected
    # ------------------------------------------------------------------
    def _r01_leak_events(self, s: AnalyticsSummary) -> List[RuleOutput]:
        leak = s.leak_summary
        if leak.total_leaks < self.LEAK_TRIGGER_COUNT:
            return []

        shutoff_note = (
            f"{leak.auto_shutoffs_triggered} auto-shutoff(s) were triggered."
            if leak.auto_shutoffs_triggered > 0
            else "No auto-shutoffs were recorded."
        )
        return [RuleOutput(
            rule_id="R01",
            category="safety",
            priority=1,
            confidence=0.98,
            message=(
                f"{leak.total_leaks} gas leak event(s) were recorded in the last {s.period_days} days. "
                f"{shutoff_note} "
                "Please review the Safety dashboard and ensure the regulator valve is closed "
                "after every use. Check all hose connections for wear or cracks."
            ),
            supporting_facts={
                "total_leaks": leak.total_leaks,
                "auto_shutoffs_triggered": leak.auto_shutoffs_triggered,
                "peak_ppm_recorded": leak.peak_ppm,
                "period_days": s.period_days,
            },
        )]

    # ------------------------------------------------------------------
    # R02 — Elevated historical gas PPM reading
    # ------------------------------------------------------------------
    def _r02_high_ppm(self, s: AnalyticsSummary) -> List[RuleOutput]:
        peak = s.leak_summary.peak_ppm
        if peak <= self.HIGH_PPM_THRESHOLD:
            return []

        # Deliberately conservative wording — this is a HISTORICAL reading,
        # NOT a claim that gas is currently leaking.
        severity_label = "critically high" if peak > 1000 else "elevated"
        return [RuleOutput(
            rule_id="R02",
            category="safety",
            priority=1,
            confidence=0.95,
            message=(
                f"A {severity_label} gas concentration of {peak:.0f} PPM was recorded during "
                f"the last {s.period_days} days. "
                "Check the Safety dashboard for details. Ensure adequate kitchen ventilation "
                "and inspect all connections. This is based on a historical sensor reading."
            ),
            supporting_facts={
                "peak_ppm_recorded": peak,
                "detection_threshold_ppm": self.HIGH_PPM_THRESHOLD,
                "period_days": s.period_days,
            },
        )]

    # ------------------------------------------------------------------
    # R03 — Rising consumption trend
    # ------------------------------------------------------------------
    def _r03_rising_trend(self, s: AnalyticsSummary) -> List[RuleOutput]:
        trend = s.trend
        # Guard: need a meaningful prior period baseline
        if trend.prior_period_avg_g <= 0:
            return []
        if trend.trend != "increasing" or trend.percent_change < self.TREND_INCREASE_PCT:
            return []

        return [RuleOutput(
            rule_id="R03",
            category="efficiency",
            priority=2,
            confidence=0.88,
            message=(
                f"Your LPG consumption has increased by {trend.percent_change:.1f}% "
                f"(recent avg: {trend.recent_period_avg_g:.0f}g/day vs "
                f"prior avg: {trend.prior_period_avg_g:.0f}g/day). "
                "Consider reviewing recent cooking habits — using lids, soaking lentils, "
                "and matching flame size to pot size can help reduce usage."
            ),
            supporting_facts={
                "recent_avg_g_per_day": round(trend.recent_period_avg_g, 1),
                "prior_avg_g_per_day": round(trend.prior_period_avg_g, 1),
                "increase_pct": trend.percent_change,
                "period_days": s.period_days,
            },
        )]

    # ------------------------------------------------------------------
    # R04 — Excessive night-time usage
    # ------------------------------------------------------------------
    def _r04_night_usage(self, s: AnalyticsSummary) -> List[RuleOutput]:
        # Guard: need at least some total consumption to compute percentages
        if s.usage_pattern.total_consumption_g <= 0:
            return []

        night_slot = next(
            (sl for sl in s.usage_pattern.slots if sl.slot_name == "Night"), None
        )
        if night_slot is None or night_slot.percentage <= self.NIGHT_USAGE_PCT:
            return []

        return [RuleOutput(
            rule_id="R04",
            category="efficiency",
            priority=2,
            confidence=0.82,
            message=(
                f"{night_slot.percentage:.1f}% of your LPG usage occurred between 22:00 and 05:00 "
                f"over the last {s.period_days} days. "
                "Verify the stove is fully off before sleeping. "
                "Pre-cooking evening meals during daytime hours can reduce overnight usage."
            ),
            supporting_facts={
                "night_usage_pct": round(night_slot.percentage, 1),
                "night_consumption_g": round(night_slot.consumption_g, 1),
                "threshold_pct": self.NIGHT_USAGE_PCT,
                "period_days": s.period_days,
            },
        )]

    # ------------------------------------------------------------------
    # R05 — Low efficiency grade (C or D)
    # ------------------------------------------------------------------
    def _r05_low_efficiency_grade(self, s: AnalyticsSummary) -> List[RuleOutput]:
        eff = s.efficiency
        if eff.grade not in self.LOW_EFFICIENCY_GRADES:
            return []

        deductions: list = eff.components_json.get("deductions", [])
        issues_text = "; ".join(deductions) if deductions else "multiple efficiency issues were detected"

        return [RuleOutput(
            rule_id="R05",
            category="efficiency",
            priority=2,
            confidence=round(0.60 + (100.0 - eff.overall_score) / 100.0 * 0.35, 2),
            message=(
                f"Your LPG efficiency score is {eff.overall_score:.0f}/100 (Grade {eff.grade}). "
                f"Issues identified: {issues_text}. "
                "Reducing late-night usage, addressing any leak events, and keeping a "
                "consistent cooking schedule can improve your grade."
            ),
            supporting_facts={
                "overall_score": eff.overall_score,
                "grade": eff.grade,
                "issues": deductions,
                "period_days": s.period_days,
            },
        )]

    # ------------------------------------------------------------------
    # R06 — Heavy average daily consumption
    # ------------------------------------------------------------------
    def _r06_heavy_daily_use(self, s: AnalyticsSummary) -> List[RuleOutput]:
        avg_g = s.averages.avg_daily_g
        # Guard: need at least a few days of data
        if s.averages.total_days_analyzed < 3 or avg_g <= self.HEAVY_USE_G_PER_DAY:
            return []

        return [RuleOutput(
            rule_id="R06",
            category="efficiency",
            priority=3,
            confidence=0.80,
            message=(
                f"Your average daily LPG consumption is {avg_g:.0f}g over the last "
                f"{s.period_days} days. This is above the 600g/day threshold. "
                "Reviewing your cooking techniques — using lids, pressure cooking, and "
                "correct flame sizes — may help bring this down."
            ),
            supporting_facts={
                "avg_daily_g": round(avg_g, 1),
                "days_analyzed": s.averages.total_days_analyzed,
                "threshold_g": self.HEAVY_USE_G_PER_DAY,
                "period_days": s.period_days,
            },
        )]

    # ------------------------------------------------------------------
    # R07 — Specific dish over-consuming gas vs its stored base expectation
    # NOTE: base_gas_g is read from the Dish record in the database (dish_library
    # table), not invented. Sessions without a linked Dish are skipped.
    # ------------------------------------------------------------------
    def _r07_overconsumption_vs_dish(
        self, cooking_history: List[CookingHistory]
    ) -> List[RuleOutput]:
        outputs: List[RuleOutput] = []
        flagged_dish_ids: set = set()

        for session in cooking_history:
            dish = getattr(session, "dish", None)
            if dish is None:
                continue
            actual_g = session.actual_gas_g
            base_g = getattr(dish, "base_gas_g", None)
            if actual_g is None or base_g is None or base_g <= 0:
                continue

            dish_id = getattr(dish, "id", None)
            if dish_id in flagged_dish_ids:
                continue  # only one tip per distinct dish

            if actual_g > self.OVERCONSUMPTION_FACTOR * base_g:
                excess_pct = round((actual_g - base_g) / base_g * 100)
                flagged_dish_ids.add(dish_id)
                outputs.append(RuleOutput(
                    rule_id="R07",
                    category="cooking",
                    priority=3,
                    confidence=0.78,
                    message=(
                        f"Cooking '{dish.dish_name}' used {actual_g:.0f}g of LPG — "
                        f"{excess_pct}% more than the recorded baseline of {base_g:.0f}g. "
                        "Try soaking ingredients beforehand, using the correct pot size, "
                        "and reducing the flame once boiling starts."
                    ),
                    supporting_facts={
                        "dish_name": dish.dish_name,
                        "actual_gas_g": round(actual_g, 1),
                        "baseline_gas_g": round(base_g, 1),
                        "excess_pct": excess_pct,
                    },
                ))
                if len(outputs) >= 2:   # cap at 2 dish tips per generation call
                    break

        return outputs

    # ------------------------------------------------------------------
    # R08 — Infrequent cooking sessions logged
    # Guard: only fire when there is actually insufficient data, not when
    # the user genuinely cooks very little.
    # ------------------------------------------------------------------
    def _r08_infrequent_cooking(
        self, cooking_history: List[CookingHistory]
    ) -> List[RuleOutput]:
        count = len(cooking_history)
        if count >= self.MIN_COOKING_SESSIONS:
            return []

        return [RuleOutput(
            rule_id="R08",
            category="cooking",
            priority=4,
            confidence=0.65,
            message=(
                f"Only {count} cooking session(s) have been logged recently. "
                "Logging dishes in the Cooking Assistant gives the recommendation "
                "engine enough data to produce dish-specific gas-saving tips."
            ),
            supporting_facts={
                "sessions_logged": count,
                "minimum_for_dish_analysis": self.MIN_COOKING_SESSIONS,
            },
        )]

    # ------------------------------------------------------------------
    # R09 — Refill recommended based on existing RefillPrediction record
    # This rule is ONLY fired when a prediction record already exists in
    # the database. It never estimates or invents remaining gas levels.
    # ------------------------------------------------------------------
    def _r09_refill_soon(
        self, latest_refill_prediction: Optional[RefillPrediction]
    ) -> List[RuleOutput]:
        if latest_refill_prediction is None:
            return []   # no prediction data — skip rule entirely

        days_left = latest_refill_prediction.days_left
        if days_left > self.REFILL_DAYS_LEFT:
            return []

        return [RuleOutput(
            rule_id="R09",
            category="refill",
            priority=2,
            confidence=round(min(0.95, latest_refill_prediction.confidence), 2),
            message=(
                f"Your cylinder is predicted to run out in approximately {days_left} day(s). "
                "Schedule a refill soon to avoid interruption. "
                "Visit the Cylinder page for the full refill prediction."
            ),
            supporting_facts={
                "days_left": days_left,
                "prediction_confidence": latest_refill_prediction.confidence,
                "predicted_empty_date": str(
                    latest_refill_prediction.predicted_empty_date.date()
                ),
            },
        )]

    # ------------------------------------------------------------------
    # R10 — Highly erratic / volatile daily consumption
    # ------------------------------------------------------------------
    def _r10_consumption_volatility(self, s: AnalyticsSummary) -> List[RuleOutput]:
        vals = [d.consumption_g for d in s.daily.records if d.consumption_g > 0]
        if len(vals) < self.MIN_ACTIVE_DAYS_FOR_VOLATILITY:
            return []   # not enough data for a meaningful variance estimate

        mean = sum(vals) / len(vals)
        if mean <= 0:
            return []

        variance = sum((x - mean) ** 2 for x in vals) / len(vals)
        std_dev = math.sqrt(variance)

        if std_dev <= self.VOLATILITY_FACTOR * mean:
            return []

        cv = round(std_dev / mean * 100, 1)
        return [RuleOutput(
            rule_id="R10",
            category="efficiency",
            priority=3,
            confidence=0.74,
            message=(
                f"Your daily LPG usage is highly variable (coefficient of variation: {cv}%) "
                f"over {len(vals)} active day(s). "
                "Large swings often indicate prolonged idle burner time or unplanned cooking. "
                "A more consistent cooking schedule reduces waste and improves predictability."
            ),
            supporting_facts={
                "mean_g_per_day": round(mean, 1),
                "std_dev_g": round(std_dev, 1),
                "coefficient_of_variation_pct": cv,
                "active_days_analyzed": len(vals),
            },
        )]


# Singleton — import this where the engine is needed
recommendation_engine = RecommendationEngine()
