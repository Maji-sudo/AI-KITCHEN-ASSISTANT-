# app/services/safety_classification.py
"""Safety classification logic for gas ppm values.

Provides a single authoritative function `classify_gas` that maps a numeric
ppm reading to one of the status strings defined by the project:

- "normal"   : ppm < 500
- "warning"  : 500 <= ppm < 1000
- "critical" : ppm >= 1000

The thresholds are defined centrally in ``app.services.telemetry_service`` to
avoid duplication.
"""

from app.services.telemetry_service import PPM_WARNING_THRESHOLD, PPM_CRITICAL_THRESHOLD


def classify_gas(ppm: float) -> str:
    """Classify a gas reading according to project thresholds.

    Args:
        ppm: The measured parts‑per‑million value.

    Returns:
        A string status – ``"normal"``, ``"warning"`` or ``"critical"``.
    """
    if ppm >= PPM_CRITICAL_THRESHOLD:
        return "critical"
    if ppm >= PPM_WARNING_THRESHOLD:
        return "warning"
    return "normal"
