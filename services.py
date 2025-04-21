import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import openai
import json_repair
from fastapi import HTTPException
from openai import OpenAI
from models import (
    MealPlanRequest,
    MealPlanResponse,
    ShoppingListItem,
    Day,
    Meal,
    Recipe,
    Ingredient,
)

load_dotenv()


class MealPlanService:
    def __init__(self):
        """Initialize the OpenAI client."""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    async def generate_meal_plan(self, request: MealPlanRequest) -> Day:
        system_message = """You are a professional chef and nutritionist. Your task is to generate a detailed meal plan based on the user's requirements.
        The meal plan should follow this format:
        {
            "days": [
                {
                    "meals": [
                        {
                            "meal_type": "breakfast" | "dinner" | "lunch" | "snack",
                            "recipes": [
                                {
                                    "recipe_type": "collation" | "starter" | "main" | "dessert",
                                    "recipe": {
                                        "name": string,
                                        "ingredients": [
                                            {
                                                "label": string,
                                                "quantity": number,
                                                "unit": string
                                            }
                                        ],
                                        "steps": {
                                            "1": string,
                                            "2": string,
                                            ...
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }"""

        user_message = f"""Based on the following input, generate a detailed meal plan:

Input JSON:
```json
{request.json()}
```

For each day, provide ONLY ASKED MEALS and respect these rules:
- Lunch and dinner should include three recipes each: a starter, a main course, and a dessert
- Breakfast and snacks should include one recipe each
- All recipes should include a list of ingredients with quantities and units
- All recipes should include step-by-step instructions
- The meal plan should be nutritionally balanced and follow any dietary restrictions specified in the input"""

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=4000,
        )

        try:
            meal_plan = json.loads(response.choices[0].message.content)
            return Day(**meal_plan)
        except Exception as e:
            print(f"Error parsing meal plan: {str(e)}")
            print(f"Raw response: {response.choices[0].message.content}")
            raise

    async def generate_shopping_list(self, meal_plan: Day) -> List[ShoppingListItem]:
        print("Starting shopping list generation...")

        # Extract all ingredients from the meal plan
        all_ingredients = []
        for day in meal_plan.days:
            for meal in day.meals:
                for recipe in meal.recipes:
                    all_ingredients.extend(recipe.recipe.ingredients)

        print(f"Found {len(all_ingredients)} ingredients in meal plan")

        if not all_ingredients:
            print("No ingredients found in meal plan")
            return []

        system_message = """You are a professional chef. Your task is to generate a consolidated shopping list from the provided ingredients.
        The shopping list should follow this format:
        [
            {
                "label": string,
                "quantity": number,
                "unit": string
            }
        ]
        
        Rules for the shopping list:
        1. Combine similar ingredients and sum their quantities
        2. Use consistent units (e.g., convert all weights to grams, all volumes to milliliters)
        3. Round quantities to reasonable numbers
        4. Remove any duplicate entries
        5. Sort ingredients alphabetically"""

        user_message = f"""Generate a consolidated shopping list from these ingredients:
```json
{json.dumps([ingredient.dict() for ingredient in all_ingredients])}
```"""

        response = await self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=2000,
        )

        print(f"Raw shopping list response: {response.choices[0].message.content}")

        try:
            shopping_list = json.loads(response.choices[0].message.content)
            if isinstance(shopping_list, list):
                return [ShoppingListItem(**item) for item in shopping_list]
            elif isinstance(shopping_list, dict) and "shopping_list" in shopping_list:
                return [
                    ShoppingListItem(**item) for item in shopping_list["shopping_list"]
                ]
            else:
                print(f"Unexpected shopping list format: {type(shopping_list)}")
                return []
        except Exception as e:
            print(f"Error parsing shopping list: {str(e)}")
            return []

    def _add_dates_to_meal_plan(self, meal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Add dates to the meal plan."""
        today = datetime.now()
        for i, day in enumerate(meal_plan["days"]):
            date = today + timedelta(days=i)
            day["date"] = date.strftime("%Y-%m-%d")
        return meal_plan

    def _standardize_units(self, shopping_list: List[Dict]) -> List[Dict]:
        """Standardize units in the shopping list."""
        unit_mapping = {
            # Teaspoons
            "tsp": "teaspoon",
            "tsps": "teaspoons",
            "tsp.": "teaspoon",
            "tsps.": "teaspoons",
            "teaspoon": "teaspoon",
            "teaspoons": "teaspoons",
            # Tablespoons
            "tbsp": "tablespoon",
            "tbsps": "tablespoons",
            "tbsp.": "tablespoon",
            "tbsps.": "tablespoons",
            "tablespoon": "tablespoon",
            "tablespoons": "tablespoons",
            # Cups
            "cup": "cup",
            "cups": "cups",
            "c.": "cup",
            "c.": "cups",
            # Grams
            "g": "gram",
            "gs": "grams",
            "g.": "gram",
            "gs.": "grams",
            "gram": "gram",
            "grams": "grams",
            # Milliliters
            "ml": "milliliter",
            "mls": "milliliters",
            "ml.": "milliliter",
            "mls.": "milliliters",
            "milliliter": "milliliter",
            "milliliters": "milliliters",
            # Whole items
            "whole": "piece",
            "wholes": "pieces",
            "pc": "piece",
            "pcs": "pieces",
            "piece": "piece",
            "pieces": "pieces",
            # Other common units
            "pinch": "pinch",
            "pinches": "pinches",
            "medium": "piece",
            "large": "piece",
            "small": "piece",
        }

        standardized_list = []
        for item in shopping_list:
            # Create a copy of the item to avoid modifying the original
            standardized_item = item.copy()

            # Standardize the unit if it exists in our mapping
            if "unit" in standardized_item:
                unit = standardized_item["unit"].lower()
                if unit in unit_mapping:
                    standardized_item["unit"] = unit_mapping[unit]

            standardized_list.append(standardized_item)

        return standardized_list
