"""
serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

class UserSerializer(serializers.ModelSerializer):
    """ serializer for the user object"""

    class Meta:

        model= get_user_model()