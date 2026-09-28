"""
api tests for ingredients

"""


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


def create_user(email = 'user@example.com', password='testpass123'):
    """ create and return a new user"""

    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientsApiTests(TestCase):
    """ test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()


    def test_auth_required(self):
        """test atuth is required for retrieving ingredients"""

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientsApiTests(TestCase):
    """test authenticated API requests"""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """test retrieving a list of ingredients"""

        Ingredient.objects.create(user=self.user, name='Momos')
        Ingredient.objects.create(user=self.user, name='Chowmein')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)


    def test_ingredients_limited_to_user(self):
        """test list of ingredient is limited to authenticated user"""