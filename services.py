import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dotenv import load_dotenv
import openai
import json_repair
import httpx

load_dotenv()


class MealPlanService:
    def __init__(self):
        # Initialize the OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # Create a basic httpx client without proxy settings
        http_client = httpx.Client()

        # Initialize the OpenAI client with the custom http client
        self.client = openai.OpenAI(api_key=api_key, http_client=http_client)
        self.model = "gpt-4-turbo"  # Using gpt-4-turbo which supports response_format

    def generate_meal_plan(
        self,
        days_count: int,
        meals: List[str],
        diet: str,
        excluded_ingredients: List[str],
    ) -> Dict:
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
        print("🚀 ~  _generate_meal_plan_with_openai // input_json:", input_json)

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
- Collations are simpler, single-dish meals.

Each meal should:
1. Avoid all ingredients listed in "excludedIngredients".
2. Adhere to the "diet" restrictions.
3. Ensure dishes are not repeated more than twice in the week.
4. Be simple, tasty, and quick to prepare, suitable for one adult.
5. One portion for one adult.

Structure the output as follows:
- For each day, provide details for each meal type available that day.
- For each meal, include recipes with detailed steps and ingredients."""

        # Use the OpenAI API with response_format
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    def _format_response_as_json(self, meal_plan: str) -> Dict:
        # Since we're using response_format=json_object, the response should already be valid JSON
        try:
            parsed_json = json.loads(meal_plan)
        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from the response
            json_str = self._extract_json_from_response(meal_plan)
            try:
                parsed_json = json.loads(json_str)
            except json.JSONDecodeError:
                # If still not valid, try to repair it
                try:
                    repaired_json = json_repair.repair_json(json_str)
                    parsed_json = json.loads(repaired_json)
                except Exception:
                    # If all else fails, use OpenAI to format it
                    formatted_json = self._call_openai_for_json_formatting(json_str)
                    parsed_json = json.loads(formatted_json)

        return parsed_json

    def _add_dates_to_meal_plan(self, meal_plan: Dict) -> None:
        """Add proper dates to the meal plan starting from today."""
        today = datetime.now()

        for i, day in enumerate(meal_plan.get("days", [])):
            # Calculate the date for this day (today + i days)
            current_date = today + timedelta(days=i)
            # Format the date as YYYY-MM-DD
            day["date"] = current_date.strftime("%Y-%m-%d")

    def _extract_json_from_response(self, response: str) -> str:
        # Try to find JSON in the response
        try:
            # Look for JSON-like content between triple backticks
            if "```json" in response:
                json_content = response.split("```json")[1].split("```")[0].strip()
                return json_content
            elif "```" in response:
                json_content = response.split("```")[1].split("```")[0].strip()
                return json_content
            else:
                # If no backticks, try to find content between curly braces
                start_idx = response.find("{")
                end_idx = response.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    return response[start_idx:end_idx]
                else:
                    return response
        except Exception:
            return response

    def _call_openai_for_json_formatting(self, json_str: str) -> str:
        prompt = self._create_json_format_prompt(json_str)

        # Use the OpenAI API with response_format
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that formats data as valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content

    def _create_json_format_prompt(self, json_str: str) -> str:
        return f"""Format the following content as a valid JSON object with this structure:
{{
  "days": [
    {{
      "date": "YYYY-MM-DD",
      "meals": [
        {{
          "meal_type": "breakfast/lunch/dinner",
          "recipes": [
            {{
              "recipe_type": "starter/main/dessert",
              "recipe": {{
                "name": "Recipe Name",
                "ingredients": [
                  {{
                    "label": "Ingredient Name",
                    "quantity": 2,
                    "unit": "unit"
                  }}
                ],
                "steps": {{
                  "1": "Step description",
                  "2": "Step description"
                }}
              }}
            }}
          ]
        }}
      ]
    }}
  ],
  "shopping_list": null
}}

Content to format:
{json_str}

Make sure the JSON is valid and follows the structure above. Do not include any explanations or text outside the JSON object."""

    def _generate_shopping_list(self, meal_plan: Dict) -> List[Dict]:
        """Generate a consolidated shopping list from all recipes in the meal plan."""
        # System message with format specifications
        print("🚀 ~ _generate_shopping_list // meal_plan:", meal_plan)
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
        user_message = f"""Given this meals plan:
```json
{json.dumps(meal_plan)}
```

Create a consolidated shopping list by:
1. Combining similar ingredients
2. Summing their quantities when units match
3. Organizing by category (produce, dairy, etc.)

Return ONLY the shopping list as an array of ingredients. Each ingredient is an object with a label:string, a quantity:number and a unit:string (mL, g, etc.). Order the ingredients by similarity (ex: all vegetables together).

DO NOT return the entire meal plan, ONLY the shopping list array."""

        # Use the OpenAI API with response_format
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        shopping_list_json = response.choices[0].message.content

        # Parse the JSON response
        try:
            result = json.loads(shopping_list_json)

            # Check if the result is a dictionary with a shopping_list key
            if isinstance(result, dict) and "shopping_list" in result:
                return result["shopping_list"]

            # Check if the result is already a list (direct shopping list)
            if isinstance(result, list):
                return result

            # If it's a dictionary but doesn't have a shopping_list key, try to find a list
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, list):
                        return value

            # If we can't find a list, return an empty list
            return []

        except json.JSONDecodeError:
            # If parsing fails, try to extract JSON from the response
            extracted_json = self._extract_json_from_response(shopping_list_json)
            try:
                result = json.loads(extracted_json)

                # Check if the result is a dictionary with a shopping_list key
                if isinstance(result, dict) and "shopping_list" in result:
                    return result["shopping_list"]

                # Check if the result is already a list (direct shopping list)
                if isinstance(result, list):
                    return result

                # If it's a dictionary but doesn't have a shopping_list key, try to find a list
                if isinstance(result, dict):
                    for key, value in result.items():
                        if isinstance(value, list):
                            return value

                # If we can't find a list, return an empty list
                return []

            except json.JSONDecodeError:
                # If still not valid, try to repair it
                try:
                    repaired_json = json_repair.repair_json(extracted_json)
                    result = json.loads(repaired_json)

                    # Check if the result is a dictionary with a shopping_list key
                    if isinstance(result, dict) and "shopping_list" in result:
                        return result["shopping_list"]

                    # Check if the result is already a list (direct shopping list)
                    if isinstance(result, list):
                        return result

                    # If it's a dictionary but doesn't have a shopping_list key, try to find a list
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if isinstance(value, list):
                                return value

                    # If we can't find a list, return an empty list
                    return []

                except Exception:
                    # If all else fails, return an empty list
                    return []
