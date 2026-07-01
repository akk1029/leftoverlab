"""ORM models. Importing this package registers every table on ``Base.metadata``."""
from app.core.ids import IdCounter  # noqa: F401
from app.models.community import Comment, Post  # noqa: F401
from app.models.ingredient import Ingredient  # noqa: F401
from app.models.mealplan import MealPlan, MealPlanEntry  # noqa: F401
from app.models.recipe import Recipe, SavedRecipe  # noqa: F401
from app.models.shopping import ShoppingList, ShoppingListItem  # noqa: F401
from app.models.sustainability import SustainabilityRecord  # noqa: F401
from app.models.user import User  # noqa: F401
