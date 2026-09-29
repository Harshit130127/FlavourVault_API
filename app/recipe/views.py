""""views for recipe APIs"""


from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers




@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                name='tags',
                type=OpenApiTypes.LIST,
                location=OpenApiParameter.QUERY,
                description='Filter by tag IDs',
            ),
            OpenApiParameter(
                name='ingredients',
                type=OpenApiTypes.LIST,
                location=OpenApiParameter.QUERY,
                description='Filter by ingredient IDs',
            ),
        ]
    )
)


class RecipeViewSet(viewsets.ModelViewSet):
    """ view for manage recipe APIs"""

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)


    def _params_to_ints(self, qs):
        """convert a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(',')]


    def get_queryset(self):
        """return objects for the current authenticated user only"""
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        queryset = self.queryset.filter(user=self.request.user)
        if tags:
            tag_ids = self._params_to_ints(tags)
            queryset = queryset.filter(tags__id__in=tag_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)

        return queryset.filter(user=self.request.user).order_by('-id').distinct()


    def get_serializer_class(self):
        """return appropriate serializer class"""

        if self.action == 'list':
            return serializers.RecipeSerializer

        if self.action == 'upload_image':
            return serializers.RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """create a new recipe"""
        serializer.save(user=self.request.user)


    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        """upload an image to recipe"""
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

class BaseRecipeAttrViewSet(viewsets.GenericViewSet,
                        mixins.ListModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin):
    """base viewset for user owned recipe attributes"""
    authentication_classes = [TokenAuthentication,]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """return objects for the current authenticated user only"""
        return self.queryset.filter(user=self.request.user).order_by('-name')

class TagViewSet(BaseRecipeAttrViewSet):
    """ view for manage tag APIs"""

    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()





class IngredientViewSet(BaseRecipeAttrViewSet):
    """ view for manage ingredient APIs"""

    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


