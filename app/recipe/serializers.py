""" serializers for recipe APIs"""

from rest_framework import serializers

from core.models import Recipe, Tag




class TagSerializer(serializers.ModelSerializer):
    """ serializer for tag objects"""

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializer(serializers.ModelSerializer):
    """ serializer for recipes objects"""

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link','tags']
        read_only_fields = ['id']

    def create(self, validated_data):
        """create and return a new recipe"""

        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context['request'].user




class RecipeDetailSerializer(RecipeSerializer):
    """serializer for recipe detail view"""

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']


