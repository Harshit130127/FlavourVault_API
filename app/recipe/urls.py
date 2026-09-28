""" URL mapping for the recipe API"""

from django.urls import path,include

from recipe import views

app_name = 'recipe'


from rest_framework.routers import DefaultRouter

router = DefaultRouter()


"""Associate this URL prefix with this ViewSet, and generate the appropriate API URLs for it."""
router.register('recipes', views.RecipeViewSet)
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredientViewSet)


urlpatterns = [
    path('', include(router.urls)),

]