# 🍽️ Eatzy - AI Meal Planner API

A FastAPI-based meal planning API that generates personalized meal plans based on your dietary preferences and restrictions. This API uses OpenAI's GPT models to create detailed meal plans with recipes, ingredients, and cooking instructions.

## 🌟 Features

-   🥗 Generate personalized meal plans based on dietary preferences
-   📝 Detailed recipes with ingredients and step-by-step cooking instructions
-   🛒 Consolidated shopping list for all ingredients
-   🥘 Support for multiple meal types (breakfast, lunch, dinner)
-   🚫 Exclude specific ingredients from your meal plan
-   🔄 Flexible meal plan duration (1-7 days)

## 🚀 Getting Started

### Prerequisites

-   Python 3.8 or higher
-   OpenAI API key

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/eatzy-fastapi.git
    cd eatzy-fastapi
    ```

2. Create and activate a virtual environment:

    ```bash
    # On macOS/Linux
    python -m venv venv
    source venv/bin/activate

    # On Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Create a `.env` file in the root directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY=your_api_key_here
    ```

### 🏃‍♂️ Running the Application

1. Start the FastAPI server:

    ```bash
    uvicorn main:app --reload
    ```

2. The API will be available at `http://localhost:8000`

3. Access the API documentation at `http://localhost:8000/docs`

## 📝 API Usage

### Generate Meal Plan

**Endpoint:** `POST /generate-meal-plan`

**Request Body:**

```json
{
	"daysCount": 2,
	"meals": ["breakfast", "lunch", "dinner"],
	"diet": "vegetarian",
	"excludedIngredients": ["nuts", "shellfish"]
}
```

**Response:**

```json
{
	"days": [
		{
			"date": "Day 1",
			"meals": [
				{
					"meal_type": "breakfast",
					"recipes": [
						{
							"recipe_type": "main",
							"recipe": {
								"name": "Recipe Name",
								"ingredients": [
									{
										"label": "Ingredient",
										"quantity": 2,
										"unit": "unit"
									}
								],
								"steps": {
									"1": "Step description"
								}
							}
						}
					]
				}
			]
		}
	],
	"shopping_list": [
		{
			"label": "Ingredient",
			"quantity": 2,
			"unit": "unit"
		}
	]
}
```

## 🚀 Deployment to Vercel

1. Install Vercel CLI:

    ```bash
    npm install -g vercel
    ```

2. Login to Vercel:

    ```bash
    vercel login
    ```

3. Deploy the application:

    ```bash
    vercel
    ```

4. For production deployment:
    ```bash
    vercel --prod
    ```

## 🧪 Testing

Run the test script to verify the API functionality:

```bash
python test_api.py
```

## 📚 Project Structure

```
eatzy-fastapi/
├── main.py           # FastAPI application and endpoints
├── models.py         # Pydantic models for request/response validation
├── services.py       # Business logic and OpenAI integration
├── requirements.txt  # Python dependencies
├── .env             # Environment variables
└── vercel.json      # Vercel deployment configuration
```

## 🤝 Contributing

Feel free to submit issues and pull requests!

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

-   OpenAI for providing the GPT models
-   FastAPI for the amazing web framework
-   All contributors and users of this project
