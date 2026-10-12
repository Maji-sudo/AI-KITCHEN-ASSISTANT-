"""
SafeGas AI — Deterministic Dish Catalogue & Benchmark Database

Provides standard Indian household dish benchmarks for LPG consumption, cooking duration,
ingredients, serving baselines, and documented scientific/practical assumptions.
No paid AI APIs or internet access required.
"""

from typing import List, Dict, Any, Optional

DISH_CATALOGUE: List[Dict[str, Any]] = [
    {
        "id": 1,
        "dish_name": "Steamed Basmati Rice",
        "cuisine_tag": "Indian Staple",
        "ingredients": ["Basmati Rice (200g)", "Water (400ml)", "Salt", "Ghee (1 tsp)"],
        "base_servings": 2,
        "prep_duration_min": 5,
        "base_duration_min": 15,
        "base_gas_g": 35.0,
        "benchmark_assumptions": "Pre-soaked for 20 min; cooked in covered stainless steel pot on medium flame.",
        "uncertainty_margin": "±10% (31g – 39g) depending on burner power and pre-soak time.",
    },
    {
        "id": 2,
        "dish_name": "Dal Tadka",
        "cuisine_tag": "North Indian",
        "ingredients": ["Toor Dal (150g)", "Tomatoes", "Onions", "Ghee", "Cumin", "Garlic", "Turmeric"],
        "base_servings": 2,
        "prep_duration_min": 10,
        "base_duration_min": 22,
        "base_gas_g": 55.0,
        "benchmark_assumptions": "Pressure cooked (3 whistles) + 5 min aromatic tempering in separate pan.",
        "uncertainty_margin": "±12% (48g – 62g) depending on pressure cooker gasket seal and dal hardness.",
    },
    {
        "id": 3,
        "dish_name": "Vegetable Rava Upma",
        "cuisine_tag": "South Indian",
        "ingredients": ["Roasted Semolina (Rava 150g)", "Mustard Seeds", "Curry Leaves", "Carrots", "Green Chillies", "Oil"],
        "base_servings": 2,
        "prep_duration_min": 8,
        "base_duration_min": 12,
        "base_gas_g": 30.0,
        "benchmark_assumptions": "Single kadai saute and rapid boil with lid closed during water absorption.",
        "uncertainty_margin": "±10% (27g – 33g) based on flame height.",
    },
    {
        "id": 4,
        "dish_name": "Phulka / Chapati (6 pcs)",
        "cuisine_tag": "Indian Staple",
        "ingredients": ["Whole Wheat Atta (200g)", "Water", "Oil (1 tsp)", "Ghee for brushing"],
        "base_servings": 2,
        "prep_duration_min": 15,
        "base_duration_min": 15,
        "base_gas_g": 45.0,
        "benchmark_assumptions": "Heavy cast-iron tawa preheated 2 min; direct burner flame puffing.",
        "uncertainty_margin": "±15% (38g – 52g) depending on tawa preheating and rolling thickness.",
    },
    {
        "id": 5,
        "dish_name": "Crispy Masala Dosa (3 pcs)",
        "cuisine_tag": "South Indian",
        "ingredients": ["Fermented Rice-Urad Batter (300ml)", "Spiced Potato Mash", "Mustard Seeds", "Oil / Ghee"],
        "base_servings": 2,
        "prep_duration_min": 10,
        "base_duration_min": 14,
        "base_gas_g": 40.0,
        "benchmark_assumptions": "Flat iron tawa on medium heat; 3.5–4.5 minutes per dosa with lid steaming.",
        "uncertainty_margin": "±12% (35g – 45g) influenced by tawa thickness and heat retention.",
    },
    {
        "id": 6,
        "dish_name": "Steamed Idli (8 pcs)",
        "cuisine_tag": "South Indian",
        "ingredients": ["Fermented Idli Batter (400ml)", "Water for steamer (500ml)"],
        "base_servings": 2,
        "prep_duration_min": 5,
        "base_duration_min": 12,
        "base_gas_g": 28.0,
        "benchmark_assumptions": "Multi-tier idli steamer pot with tight lid on high flame.",
        "uncertainty_margin": "±10% (25g – 31g) depending on water volume and lid steam tightness.",
    },
    {
        "id": 7,
        "dish_name": "Mixed Vegetable Curry",
        "cuisine_tag": "Homestyle",
        "ingredients": ["Potatoes", "Cauliflower", "Green Peas", "Onions", "Tomatoes", "Garam Masala", "Oil"],
        "base_servings": 2,
        "prep_duration_min": 15,
        "base_duration_min": 25,
        "base_gas_g": 65.0,
        "benchmark_assumptions": "Saute 8 min + covered simmer 15 min on low flame in thick kadai.",
        "uncertainty_margin": "±12% (57g – 73g) depending on cut vegetable size and gravy consistency.",
    },
    {
        "id": 8,
        "dish_name": "Egg Bhurji / Omelette",
        "cuisine_tag": "Quick Meals",
        "ingredients": ["3 Whole Eggs", "Finely Chopped Onions", "Tomatoes", "Green Chillies", "Butter / Oil"],
        "base_servings": 2,
        "prep_duration_min": 6,
        "base_duration_min": 10,
        "base_gas_g": 22.0,
        "benchmark_assumptions": "Quick scramble in skillet on medium-high burner flame.",
        "uncertainty_margin": "±10% (20g – 25g) depending on pan thermal mass.",
    },
    {
        "id": 9,
        "dish_name": "Masala Chai (2 Cups)",
        "cuisine_tag": "Beverage",
        "ingredients": ["Water (200ml)", "Milk (150ml)", "CTC Black Tea", "Crushed Ginger", "Cardamom", "Sugar"],
        "base_servings": 2,
        "prep_duration_min": 3,
        "base_duration_min": 8,
        "base_gas_g": 18.0,
        "benchmark_assumptions": "Boiled in stainless steel saucepan; 3 min rolling simmer on low-medium flame.",
        "uncertainty_margin": "±10% (16g – 20g) depending on initial milk temperature and vessel diameter.",
    },
    {
        "id": 10,
        "dish_name": "Paneer Butter Masala",
        "cuisine_tag": "North Indian",
        "ingredients": ["Paneer (200g)", "Tomato Puree", "Butter (2 tbsp)", "Fresh Cream", "Kasuri Methi", "Spices"],
        "base_servings": 2,
        "prep_duration_min": 12,
        "base_duration_min": 25,
        "base_gas_g": 75.0,
        "benchmark_assumptions": "Puree reduction on medium heat + slow simmer with lid on low heat.",
        "uncertainty_margin": "±15% (64g – 86g) based on gravy reduction preference.",
    },
    {
        "id": 11,
        "dish_name": "Chicken Biryani",
        "cuisine_tag": "Hyderabadi",
        "ingredients": ["Basmati Rice (300g)", "Chicken (350g)", "Yogurt", "Fried Onions", "Biryani Spices", "Ghee"],
        "base_servings": 2,
        "prep_duration_min": 25,
        "base_duration_min": 45,
        "base_gas_g": 130.0,
        "benchmark_assumptions": "Parboiling rice + dum cooking for 25 min in heavy bottom sealed handi.",
        "uncertainty_margin": "±15% (110g – 150g) influenced by tawa diffuser and pot insulation.",
    },
]

DISH_BY_NAME = {d["dish_name"].lower(): d for d in DISH_CATALOGUE}


def get_catalogue_item(dish_id: int) -> Optional[Dict[str, Any]]:
    for d in DISH_CATALOGUE:
        if d["id"] == dish_id:
            return d
    return None


def get_catalogue_item_by_name(name: str) -> Optional[Dict[str, Any]]:
    name_clean = name.strip().lower()
    if name_clean in DISH_BY_NAME:
        return DISH_BY_NAME[name_clean]
    for key, val in DISH_BY_NAME.items():
        if key in name_clean or name_clean in key:
            return val
    return None


def sync_dishes_to_db(db) -> None:
    """
    Idempotently syncs catalogue dishes into the database dish_library table.
    Ensures primary keys and names exist for foreign key relationships.
    """
    from app.models.dish import Dish
    existing = {d.dish_name.lower(): d for d in db.query(Dish).all()}

    for item in DISH_CATALOGUE:
        if item["dish_name"].lower() not in existing:
            new_dish = Dish(
                dish_name=item["dish_name"],
                cuisine_tag=item["cuisine_tag"],
                base_gas_g=item["base_gas_g"],
                base_duration_min=item["base_duration_min"],
            )
            db.add(new_dish)
    db.commit()
