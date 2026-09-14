from typing import List, Optional
import os
import logging

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.cooking_repository import (
    dish_repo,
    cooking_history_repo,
)

from app.schemas.cooking import (
    DishCreate,
    CookingHistoryCreate,
    CookingHistoryUpdate,
)

from app.models.dish import Dish
from app.models.cooking_history import CookingHistory


# Load variables from .env
load_dotenv()
logger = logging.getLogger(__name__)


class CookingService:

    # ============================================================
    # DISH MANAGEMENT
    # ============================================================

    def get_dish(
        self,
        db: Session,
        dish_id: int
    ) -> Optional[Dish]:

        return dish_repo.get(
            db,
            id=dish_id
        )


    def add_dish(
        self,
        db: Session,
        dish_in: DishCreate
    ) -> Dish:

        return dish_repo.create(
            db,
            obj_in=dish_in
        )


    def get_all_dishes(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dish]:

        return dish_repo.get_multi(
            db,
            skip=skip,
            limit=limit
        )


    # ============================================================
    # COOKING HISTORY
    # ============================================================

    def record_cooking_session(
        self,
        db: Session,
        session_in: CookingHistoryCreate
    ) -> CookingHistory:

        return cooking_history_repo.create(
            db,
            obj_in=session_in
        )


    def update_cooking_session(
        self,
        db: Session,
        session_id: int,
        session_in: CookingHistoryUpdate
    ) -> Optional[CookingHistory]:

        db_session = cooking_history_repo.get(
            db,
            id=session_id
        )

        if db_session:

            return cooking_history_repo.update(
                db,
                db_obj=db_session,
                obj_in=session_in
            )

        return None


    def get_user_history(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[CookingHistory]:

        return cooking_history_repo.get_by_user(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit
        )


    # ============================================================
    # GEMINI AI CHAT
    # ============================================================

    def get_chat_response(
        self,
        message: str
    ) -> str:
        """
        Generates an AI response for kitchen and cooking queries using Google Gemini API.
        Uses settings.GEMINI_API_KEY loaded securely from the backend environment.
        """
        if not message or not message.strip():
            return "Please enter a valid question or cooking query."

        # Read API key from settings or environment
        api_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")

        if not api_key:
            logger.warning("Gemini API key missing in settings")
            return (
                "Gemini API key is not configured. "
                "Please check your backend .env file."
            )

        try:
            from google import genai

            client = genai.Client(api_key=api_key)

            prompt = f"""You are SafeGas AI Cooking Assistant.

LPG SAFETY HAS PRIORITY OVER COOKING ADVICE.

Your job is to help Indian households with:
- LPG gas consumption estimates
- Indian cooking recipes and techniques
- Cooking time and burner flame adjustment tips
- Gas saving techniques and energy efficiency
- Kitchen safety & LPG cylinder care

Safety Rules:
1. Never recommend testing an LPG leak using matches, lighters, candles, incense sticks, any open flame, or any other ignition source.
2. If a user suspects an LPG leak or smells LPG:
   - Do not create flames, sparks, or operate electrical switches.
   - Advise them to move away from the suspected leak and evacuate to a safe/open area.
   - Instruct them to contact the appropriate LPG emergency service or qualified gas technician.
   - Only mention shutting off the LPG supply if it is immediately safe to do so without approaching the leak.
3. Do NOT provide DIY instructions for repairing LPG regulators, cylinders, valves, gas hoses, modifying gas connections, or bypassing safety devices.
4. Do NOT provide step‑by‑step DIY leak inspection procedures when an active or suspected LPG leak is reported.
5. Do NOT recommend the user approach, touch, disconnect, reconnect, tighten, loosen, or repair a gas connection when an active leak is suspected.
6. For abnormal yellow/orange flames:
   - Do not tell the user to poke burner holes with pins, wires, needles, or other sharp/metal objects.
   - Recommend turning off the appliance when safe and contacting a qualified technician if the flame persists.
7. Avoid unsupported precise claims such as "75% less fuel", "10–15% savings", "40% faster" unless the user explicitly asks for a sourced comparison.
8. Do not invent statistics, emergency numbers, technical specifications, or safety procedures.
9. For emergency situations, keep the response concise and action‑oriented rather than providing lengthy cooking advice.
10. Never claim that an LPG connection is definitely safe based only on information provided in chat.
11. If the user's question is unrelated to cooking, LPG, kitchen safety, gas usage, or the SafeGas system, politely state that you are designed to assist with SafeGas‑related topics.

Provide practical, clear, and concise answers.

User message:
{message.strip()}
"""

            # Priority list of models
            candidate_models = ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite"]

            for model_name in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                    )
                    if response and hasattr(response, "text") and response.text:
                        return response.text.strip()
                except Exception as model_err:
                    logger.warning("Gemini model %s failed: %s", model_name, type(model_err).__name__)
                    continue

            raise RuntimeError("All configured Gemini models failed to respond.")

        except Exception as e:
            logger.error("Gemini API call error: %s", type(e).__name__)

            # Fallback responses for common kitchen queries if offline or API error occurs
            lower = message.lower()
            if "dal" in lower:
                return (
                    "Dal Tadka uses approximately 45g of gas and takes about 20 minutes. "
                    "Using a pressure cooker can help save up to 30% gas."
                )
            if "rice" in lower:
                return (
                    "1 cup of rice uses approximately 25g of gas and takes around 15 minutes. "
                    "Soaking rice for 30 minutes before cooking reduces gas usage."
                )
            if "roti" in lower or "chapati" in lower:
                return (
                    "Cooking 10 rotis uses approximately 60g of gas and takes around 15 minutes. "
                    "Preheating the tawa properly saves time and fuel."
                )
            if "sambar" in lower:
                return (
                    "Sambar uses approximately 60g of gas and takes around 30 minutes."
                )
            if "gas" in lower or "save" in lower or "saving" in lower:
                return (
                    "Top Gas Saving Tips:\n"
                    "1. Keep burner flames within the pan base size.\n"
                    "2. Soak lentils and rice before boiling.\n"
                    "3. Always cover pots with lids while simmering."
                )

            return (
                "I am currently having trouble reaching the Gemini service. "
                "Please try again in a moment."
            )


# ================================================================
# SERVICE INSTANCE
# ================================================================

cooking_service = CookingService()