"""test fore recipe api"""

import tempfile
import os

from PIL import Image


from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient)


from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL= reverse('recipe:recipe-list')


def detail_url(recipe_id):
    """create and return a recipe detail url"""
    return reverse('recipe:recipe-detail', args = [recipe_id])


def image_upload_url(recipe_id):
    """create and return an image upload url"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def create_recipe(user, **params):
    """create and return a sample recipe"""

    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': 50,
        'description': 'sample recipe description',
        'link': 'https://example.com/recipe.pdf',
    }

    defaults.update(params)

    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


def create_user(**params):
    """create and return a new user"""
    return get_user_model().objects.create_user(**params)




class PublicRecipeApiTests(TestCase):
    """ test authenticated recipe API access"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email = 'user@example.com', password = 'test123')


        self.client.force_authenticate(self.user)


    def test_retrieve_recipes(self):
        """test retrieving a list of recipes"""

        create_recipe(user=self.user)
        create_recipe(user=self.user)

        res= self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data , serializer.data)


    def test_recipe_list_limited_to_user(self):
        """test list of recipes is limited to authenticated user"""


        other_user = create_user(
            email='other@example.com',
            password='password123',
        )

        create_recipe(user=other_user)
        create_recipe(user=other_user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many = True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data , serializer.data)


    def test_get_recipe_detail(self):
        """test get recipe detail"""

        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)


    def test_create_recipe(self):
        """test creating a recipe"""

        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': 50,
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)


    def test_partial_update_recipe(self):
        """test partial update of a recipe using patch """

        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link,
        )

        payload = {'title': 'Updated recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)


    def test_full_update_recipe(self):
        """ test full update of recipe using put"""

        recipe = create_recipe(
            user=self.user,
            title = 'Sample recipe title',
            link = 'https://example.com/recipe.pdf',
            description = 'sample recipe description',
        )

        payload = {
                   'title': 'new recipe title',
                   'link' : 'https://example.com/new-recipe.pdf',
                   'description' : 'new recipe description',
                   'time_minutes' : 10,
                   'price' : 50,
                   }

        url = detail_url(recipe.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)
        self.assertEqual(recipe.user, self.user)


    def test_update_user_returns_error(self):
        """test changing the recipe user results in an error"""

        new_user= create_user(email='user2@exampl.com', password='test123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)

        self.client.patch(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)


    def test_delete_recipe(self):
        """test deleting a recipe successful"""

        recipe= create_recipe(user=self.user)

        url = detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())


    def test_recipe_other_users_recipe_error(self):
        """test trying to delete another users recipe gives error"""

        new_user = create_user(
            email='user2@example.com',
            password='test123',
        )

        recipe = create_recipe(user=new_user)

        url = detail_url(recipe.id)

        res = self.client.delete(url)

        self.assertEqual(
            res.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            Recipe.objects.filter(id=recipe.id).exists()
     )



    def test_create_recipe_with_new_tags(self):
        """test creating a recipe with new tags"""

        payload = {
            'title': 'Thai Prawn Curry',
            'time_minutes': 30,
            'price': 12.00,
            'tags': [{'name': 'Thai'}, {'name': 'Dinner'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tag.count(), 2)
        for tag in payload['tags']:
            exists = recipe.tag.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_recipe_with_existing_tag(self):
        """test creating a recipe with existing tag"""

        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes': 60,
            'price': 10.00,
            'tags': [{'name': 'Indian'}, {'name': 'Breakfast'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.tag.count(), 2)
        self.assertIn(tag_indian, recipe.tag.all())
        for tag in payload['tags']:
            exists = recipe.tag.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_tag_on_update(self):
        """test creating a tag when updating a recipe"""

        recipe = create_recipe(user=self.user)

        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format = 'json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name= 'Lunch')
        self.assertIn(new_tag, recipe.tag.all())


    def test_update_recipe_assign_tag(self):
        """test assigning an existing tag when updating a recipe"""

        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user=self.user)
        recipe.tag.add(tag_breakfast)

        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        payload = {'tags': [{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag_lunch, recipe.tag.all())
        self.assertNotIn(tag_breakfast, recipe.tag.all())


    def test_clear_recipe_tags(self):
        """test clearing a recipes tags"""

        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tag.add(tag)

        payload = {'tags': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tag.count(), 0)



    def test_create_recipe_with_new_ingredient(self):
            """test creating a recipe with new ingredients"""

            payload = {
                'title': 'Pasta',
                'time_minutes': 30,
                'price': 100,
                'ingredients': [{'name': 'Tomato'}, {'name': 'Cauliflower'}]
            }

            res = self.client.post(RECIPE_URL , payload, format='json')

            self.assertEqual(res.status_code, status.HTTP_201_CREATED)
            recipe = Recipe.objects.filter(user=self.user)
            self.assertEqual(recipe.count(), 1)
            recipe = recipe[0]
            self.assertEqual(recipe.ingredients.count(), 2)

            for ingredient in payload['ingredients']:
                exists = recipe.ingredients.filter(
                    name=ingredient['name'],
                    user=self.user,
                ).exists()
                self.assertTrue(exists)


    def test_create_recipe_with_existing_ingredient(self):
        """test creating a recipe with existing ingredient"""

        ingredient = Ingredient.objects.create(user=self.user, name='Lentils')
        payload = {
            'title': 'Dal',
            'time_minutes': 30,
            'price': 12.00,
            'ingredients': [{'name': 'Lentils'}, {'name': 'Onion'}],
        }

        res = self.client.post(RECIPE_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(), 2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)



    def test_create_ingredient_on_update(self):
        """test creating an ingredient when updating a recipe"""

        recipe = create_recipe(user=self.user)

        payload = {'ingredients': [{'name': 'Cabbage'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user=self.user, name='Cabbage')
        self.assertIn(new_ingredient, recipe.ingredients.all())


    def test_update_recipe_assign_ingredient(self):
        """test assigning an existing ingredient when updating a recipe"""

        ingredient1 = Ingredient.objects.create(user=self.user, name='Cabbage')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user, name='Tomato')
        payload = {'ingredients': [{'name': 'Tomato'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())


    def test_clear_recipe_ingredients(self):
        """ test clearing a recipes ingredients"""

        ingredient = Ingredient.objects.create(user=self.user, name='Cabbage')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)

        payload = {'ingredients': []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


    def test_filter_recipes_by_tags(self):
        """test returning recipes with specific tags"""

        recipe1 = create_recipe(user=self.user, title='Thai vegetable curry')
        recipe2 = create_recipe(user=self.user, title='Panner chicken')
        tag1 = Tag.objects.create(user=self.user, name='Vegan')
        tag2 = Tag.objects.create(user=self.user, name='Non-Vegetarian')
        recipe1.tag.add(tag1)
        recipe2.tag.add(tag2)
        recipe3 = create_recipe(user=self.user, title='Fish and chips')

        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(
            RECIPE_URL, params
        )

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(recipe3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)


    def test_filter_recipes_by_ingredients(self):
        """test returning recipes with specific ingredients"""

        recipe1 = create_recipe(user=self.user, title='pakoda curry')
        recipe2 = create_recipe(user=self.user, title='Chicken cacciatore')
        ingredient1 = Ingredient.objects.create(user=self.user, name='Cabbage')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Chicken')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = create_recipe(user=self.user, title='Steak and mushrooms')

        params = {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        res = self.client.get(
            RECIPE_URL, params
        )

        s1 = RecipeSerializer(recipe1)
        s2 = RecipeSerializer(recipe2)
        s3 = RecipeSerializer(recipe3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)










class ImageUploadTests(TestCase):
    """tests for image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user  = get_user_model().objects.create_user(
            'user2@example.com',
            'test123',
        )

        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        """test uploading an image to recipe"""

        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))


    def test_upload_image_bad_request(self):
        """test uploading an invalid image"""

        url = image_upload_url(self.recipe.id)
        payload = {'image': 'notimage'}
        res = self.client.post(url, payload , format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)