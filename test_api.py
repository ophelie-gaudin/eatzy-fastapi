import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API URL - change this to your deployed URL when testing production
API_URL = "http://localhost:8000/generate-meal-plan"


def test_meal_plan_generation():
    """Test the meal plan generation endpoint."""
    # Test data - matches the format from the React Native app
    test_data = {
        "daysCount": 3,
        "meals": ["lunch"],  # Only requesting lunch for testing
        "diet": "vegetarian",
        "excludedIngredients": ["nuts", "shellfish"],
    }

    # Make the request
    response = requests.post(API_URL, json=test_data)

    # Check response
    if response.status_code == 200:
        result = response.json()
        print("✅ API test successful!")
        print("Response:")
        print(json.dumps(result, indent=2))

        # Validate the response format
        if "days" in result:
            days = result["days"]
            print("\n✅ Response format is correct")

            # Check if days is a list
            if isinstance(days, list):
                print(f"✅ Found {len(days)} days in the meal plan")

                # Validate that the number of days matches the request
                if len(days) == test_data["daysCount"]:
                    print(
                        f"✅ Number of days ({len(days)}) matches the request ({test_data['daysCount']})"
                    )
                else:
                    print(
                        f"❌ Number of days ({len(days)}) does not match the request ({test_data['daysCount']})"
                    )

                # Check if each day has the expected structure
                if days:
                    first_day = days[0]
                    if "date" in first_day and "meals" in first_day:
                        print(f"✅ First day has date: {first_day['date']}")

                        # Check if meals is a list
                        meals = first_day["meals"]
                        if isinstance(meals, list):
                            print(f"✅ First day has {len(meals)} meals")

                            # Validate that only the requested meal types are included
                            requested_meals = set(test_data["meals"])
                            actual_meals = set(meal["meal_type"] for meal in meals)

                            if actual_meals.issubset(requested_meals) and len(
                                actual_meals
                            ) == len(requested_meals):
                                print(
                                    f"✅ Meal types match the request: {', '.join(actual_meals)}"
                                )
                            else:
                                print(
                                    f"❌ Meal types ({', '.join(actual_meals)}) do not match the request ({', '.join(requested_meals)})"
                                )

                            # Check if each meal has the expected structure
                            if meals:
                                first_meal = meals[0]
                                if (
                                    "meal_type" in first_meal
                                    and "recipes" in first_meal
                                ):
                                    print(
                                        f"✅ First meal is of type: {first_meal['meal_type']}"
                                    )

                                    # Check if recipes is a list
                                    recipes = first_meal["recipes"]
                                    if isinstance(recipes, list):
                                        print(
                                            f"✅ First meal has {len(recipes)} recipes"
                                        )

                                        # Check if each recipe has the expected structure
                                        if recipes:
                                            first_recipe = recipes[0]
                                            if (
                                                "recipe_type" in first_recipe
                                                and "recipe" in first_recipe
                                            ):
                                                print(
                                                    f"✅ First recipe is of type: {first_recipe['recipe_type']}"
                                                )

                                                # Check if recipe has the expected structure
                                                recipe = first_recipe["recipe"]
                                                if (
                                                    "name" in recipe
                                                    and "ingredients" in recipe
                                                    and "steps" in recipe
                                                ):
                                                    print(
                                                        f"✅ Recipe has name: {recipe['name']}"
                                                    )
                                                    print(
                                                        f"✅ Recipe has {len(recipe['ingredients'])} ingredients"
                                                    )
                                                    print(
                                                        f"✅ Recipe has {len(recipe['steps'])} steps"
                                                    )
                                                else:
                                                    print(
                                                        "❌ Recipe is missing name, ingredients, or steps"
                                                    )
                                            else:
                                                print(
                                                    "❌ Recipe is missing recipe_type or recipe"
                                                )
                                        else:
                                            print("❌ No recipes found in first meal")
                                    else:
                                        print("❌ Recipes is not a list")
                                else:
                                    print("❌ Meal is missing meal_type or recipes")
                            else:
                                print("❌ No meals found in first day")
                        else:
                            print("❌ Meals is not a list")
                    else:
                        print("❌ Day is missing date or meals")
                else:
                    print("❌ No days found in meal plan")
            else:
                print("❌ Days is not a list")
        else:
            print("❌ Response does not contain 'days' key")

        # Check if shopping list is present
        if "shopping_list" in result:
            shopping_list = result["shopping_list"]
            if isinstance(shopping_list, list):
                print(f"✅ Shopping list has {len(shopping_list)} items")
            else:
                print("❌ Shopping list is not a list")
        else:
            print("❌ Response does not contain 'shopping_list' key")
    else:
        print(f"❌ API test failed with status code: {response.status_code}")
        print("Error:", response.text)


if __name__ == "__main__":
    test_meal_plan_generation()
