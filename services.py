import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv
import openai
import json_repair
from fastapi import HTTPException

load_dotenv()


class MealPlanService:
    def __init__(self):
        # Initialize the OpenAI client with the newer API
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4-turbo"  # Using gpt-4-turbo which supports response_format

    def generate_meal_plan(
        self,
        days_count: int,
        meals: List[str],
        diet: str,
        excluded_ingredients: List[str],
    ) -> Dict:
        try:
            # Generate the meal plan using OpenAI
            meal_plan = self._generate_meal_plan_with_openai(
                days_count, meals, diet, excluded_ingredients
            )

            # Format the response as JSON
            formatted_response = self._format_response_as_json(meal_plan)

            # Add proper dates to the meal plan
            self._add_dates_to_meal_plan(formatted_response)

            # Generate shopping list
            shopping_list = self._generate_shopping_list(formatted_response)

            # Add shopping list to the response
            formatted_response["shopping_list"] = shopping_list

            return formatted_response
        except Exception as e:
            # Log the error for debugging
            print(f"Error generating meal plan: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate meal plan: {str(e)}"
            )

    def _generate_meal_plan_with_openai(
        self,
        days_count: int,
        meals: List[str],
        diet: str,
        excluded_ingredients: List[str],
    ) -> str:
        # Prepare the input JSON
        input_json = {
            "daysCount": days_count,
            "meals": meals,
            "diet": diet,
            "excludedIngredients": excluded_ingredients,
        }

        # System message with format specifications
        system_message = """Respect strictly these formats :

A meals_plan is like:
{
    "days": Day[],
    "shopping_list": null
}

A Day is like:
{
    "date": string,
    "meals": Meal[]    
]
}

A Meal is like:
{
    "meal_type": "breakfast" | "dinner" | "lunch | "snack",
    "recipes": Recipe[]
}

A Recipe is like:
{
    "recipe_type": "collation" | "starter" | "main" | "dessert",
    "recipe": RecipeItem,
}

A RecipeItem is like:
{
   "name": string,
   "ingredients: Ingredient[],
   "steps": { 1: string, 2: string, ...}
}

An Ingredient is like :
{ 
   "label": string,
   "quantity": number,
   "unit":string
}"""

        # User message with the prompt
        user_message = f"""You are a professional chef and nutritionist. Based on the following input, generate a detailed meal plan. The meal plan should follow specific informations:

Input JSON:
```json
{json.dumps(input_json)}
```

For each day, provide ONLY ASKED MEALS and respect these rules:
- Lunch and dinner should include three recipes each: a starter, a main course, and a dessert.
- Breakfast should include one recipe.
- Snacks should include one recipe.
- All recipes must be suitable for the specified diet and must not include any of the excluded ingredients.
- Each recipe should include a list of ingredients with quantities and units, and step-by-step instructions.
- The meal plan should be varied and balanced, providing a good mix of nutrients.
- All recipes should be practical and feasible for home cooking.
- The meal plan should be returned in JSON format."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error in meal plan generation: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Failed to generate meal plan with OpenAI"
            )

    def _format_response_as_json(self, response: str) -> Dict:
        try:
            # Try to parse the response as JSON
            return json.loads(response)
        except json.JSONDecodeError:
            try:
                # If that fails, try to repair the JSON
                repaired_json = json_repair.loads(response)
                return repaired_json
            except Exception as e:
                print(f"Error formatting response as JSON: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Failed to format response as JSON"
                )

    def _add_dates_to_meal_plan(self, meal_plan: Dict) -> Dict:
        """Add proper dates to the meal plan starting from today."""
        today = datetime.now()

        for i, day in enumerate(meal_plan.get("days", [])):
            # Calculate the date for this day (today + i days)
            current_date = today + timedelta(days=i)
            # Format the date as YYYY-MM-DD
            day["date"] = current_date.strftime("%Y-%m-%d")

        return meal_plan

    def _generate_shopping_list(self, meal_plan: Dict) -> List[Dict]:
        try:
            print("Starting shopping list generation...")

            # Extract all ingredients from the meal plan
            all_ingredients = []
            for day in meal_plan.get("days", []):
                for meal in day.get("meals", []):
                    for recipe in meal.get("recipes", []):
                        recipe_item = recipe.get("recipe", {})
                        ingredients = recipe_item.get("ingredients", [])
                        all_ingredients.extend(ingredients)

            print(f"Extracted {len(all_ingredients)} ingredients from meal plan")

            if not all_ingredients:
                print("No ingredients found in meal plan!")
                return []

            # Create a prompt for OpenAI to clean and consolidate the shopping list
            prompt = f"""You are a helpful assistant that creates clean shopping lists in JSON format.
            Please consolidate the following ingredients into a clean shopping list.
            Combine similar ingredients and sum their quantities.
            Remove any preparation details and keep only the essential information.
            Return the result as a JSON array of ingredients with label, quantity, and unit.
            
            Ingredients:
            {json.dumps(all_ingredients)}
            
            Return ONLY the shopping list array, nothing else."""

            print("Sending request to OpenAI for shopping list generation...")

            # Call OpenAI to generate the shopping list
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates clean shopping lists in JSON format.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            print("Received response from OpenAI")

            # Parse the response
            result = json.loads(response.choices[0].message.content)
            print(f"Parsed response: {result}")

            # Ensure we return a list
            if isinstance(result, dict) and "shopping_list" in result:
                shopping_list = result["shopping_list"]
                print(f"Found shopping_list key with {len(shopping_list)} items")
                return shopping_list
            elif isinstance(result, list):
                print(f"Response is already a list with {len(result)} items")
                return result
            else:
                # If we can't find a list in the response, return an empty list
                print(f"Unexpected shopping list format: {result}")
                return []

        except Exception as e:
            print(f"Error generating shopping list: {str(e)}")
            # Return an empty list instead of failing
            return []
