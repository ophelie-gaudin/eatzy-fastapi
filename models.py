from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union, Any


class Ingredient(BaseModel):
    label: str = Field(..., description="Name of the ingredient")
    quantity: Union[int, float] = Field(..., description="Quantity of the ingredient")
    unit: str = Field(..., description="Unit of measurement")


class RecipeStep(BaseModel):
    step_number: str = Field(..., description="Step number")
    description: str = Field(..., description="Description of the step")


class Recipe(BaseModel):
    name: str = Field(..., description="Name of the recipe")
    ingredients: List[Ingredient] = Field(..., description="List of ingredients")
    steps: Dict[str, str] = Field(..., description="Step-by-step cooking instructions")


class RecipeItem(BaseModel):
    recipe_type: str = Field(..., description="Type of recipe (starter, main, dessert)")
    recipe: Recipe = Field(..., description="Recipe details")


class Meal(BaseModel):
    meal_type: str = Field(..., description="Type of meal (breakfast, lunch, dinner)")
    recipes: List[RecipeItem] = Field(..., description="List of recipes for this meal")


class Day(BaseModel):
    date: str = Field(..., description="Date of the meal plan")
    meals: List[Meal] = Field(..., description="List of meals for this day")


class ShoppingListItem(BaseModel):
    label: str = Field(..., description="Name of the ingredient")
    quantity: Union[int, float] = Field(..., description="Total quantity needed")
    unit: str = Field(..., description="Unit of measurement")


class MealPlanRequest(BaseModel):
    daysCount: int = Field(..., description="Number of days for the meal plan")
    meals: List[str] = Field(
        ...,
        description="List of meals to include (e.g., ['breakfast', 'lunch', 'dinner'])",
    )
    diet: str = Field(
        ..., description="Type of diet (e.g., 'vegetarian', 'vegan', 'keto')"
    )
    excludedIngredients: List[str] = Field(
        default_factory=list, description="List of ingredients to exclude"
    )


class MealPlanResponse(BaseModel):
    days: List[Day] = Field(..., description="List of days in the meal plan")
    shopping_list: List[ShoppingListItem] = Field(
        ..., description="Shopping list for all ingredients"
    )
