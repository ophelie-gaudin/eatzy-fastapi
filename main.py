from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from models import MealPlanRequest, MealPlanResponse
from services import MealPlanService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Eatzy Meal Planner API",
    description="API for generating personalized meal plans",
    version="1.0.0",
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


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/generate-meal-plan")
async def generate_meal_plan(request: MealPlanRequest):
    try:
        # Extract parameters from the request
        days_count = request.daysCount
        meals = request.meals
        diet = request.diet
        excluded_ingredients = request.excludedIngredients

        # Generate the meal plan
        meal_plan = meal_plan_service.generate_meal_plan(
            days_count=days_count,
            meals=meals,
            diet=diet,
            excluded_ingredients=excluded_ingredients,
        )

        return meal_plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
