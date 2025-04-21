from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import MealPlanRequest, MealPlanResponse, Day, ShoppingListItem
from services import MealPlanService
import os
from dotenv import load_dotenv
from typing import List

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Eatzy API", description="API for generating meal plans and shopping lists"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize the meal plan service
meal_plan_service = MealPlanService()


@app.post("/generate-meal-plan", response_model=MealPlanResponse)
async def generate_meal_plan(request: MealPlanRequest):
    """Generate a meal plan based on the request parameters."""
    try:
        # Generate the meal plan
        meal_plan = await meal_plan_service.generate_meal_plan(request)

        # Generate the shopping list
        shopping_list = await meal_plan_service.generate_shopping_list(meal_plan)

        return MealPlanResponse(days=meal_plan.days, shopping_list=shopping_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {"message": "Welcome to the Meal Plan API"}
