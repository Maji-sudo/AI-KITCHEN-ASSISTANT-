from typing import List, Optional
import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

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

        api_key = os.getenv("GEMINI_API_KEY")

        # --------------------------------------------------------
        # Check whether API key was loaded
        # --------------------------------------------------------

        if not api_key:

            print("======================================")
            print("GEMINI ERROR")
            print("GEMINI_API_KEY was not found.")
            print("======================================")

            return (
                "Gemini API key is not configured. "
                "Please check your .env file."
            )


        print("======================================")
        print("GEMINI API")
        print("API key detected:", api_key[:6] + "..." + api_key[-4:])
        print("User message:", message)
        print("======================================")


        # --------------------------------------------------------
        # Call Gemini
        # --------------------------------------------------------

        try:

            from google import genai
            from google.genai import types as genai_types

            client = genai.Client(
                api_key=api_key,
                http_options=genai_types.HttpOptions(timeout=30000),
            )

            prompt = f"""
You are SafeGas AI Cooking Assistant.

Your job is to help Indian households with:

- LPG gas consumption
- Indian cooking
- Cooking time estimates
- Gas saving techniques
- LPG efficiency
- Refill recommendations
- Kitchen safety

Give practical and concise answers.

User message:
{message}
"""

            # Try gemini-2.5-flash first, fall back to gemini-1.5-flash
            for model_name in ["gemini-2.5-flash", "gemini-1.5-flash"]:

                try:

                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )

                    print("======================================")
                    print(f"GEMINI SUCCESS (model: {model_name})")
                    print("======================================")

                    return response.text

                except Exception as model_err:

                    print(f"Model {model_name} failed: {model_err}")
                    continue

            raise Exception("All Gemini models failed")


        except Exception as e:

            print("======================================")
            print("GEMINI API ERROR")
            print(str(e))
            print("======================================")

            # ----------------------------------------------------
            # Development fallback
            # ----------------------------------------------------

            lower = message.lower()


            if "dal" in lower:

                return (
                    "Dal Tadka uses approximately 45g of gas "
                    "and takes about 20 minutes. "
                    "Using a pressure cooker can help save gas."
                )


            if "rice" in lower:

                return (
                    "1 cup of rice uses approximately 25g of gas "
                    "and takes around 15 minutes."
                )


            if "roti" in lower:

                return (
                    "6 rotis use approximately 30g of gas "
                    "and take around 12 minutes."
                )


            if "sambar" in lower:

                return (
                    "Sambar uses approximately 60g of gas "
                    "and takes around 30 minutes."
                )


            if (
                "gas" in lower
                or "consumption" in lower
            ):

                return (
                    "I can help estimate LPG consumption "
                    "for your cooking."
                )


            return (
                "I'm currently unable to connect to Gemini. "
                "Please check the backend terminal for the "
                "Gemini API error."
            )


# ================================================================
# SERVICE INSTANCE
# ================================================================

cooking_service = CookingService()