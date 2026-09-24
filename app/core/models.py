"""
database models
"""

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)



class UserManager(BaseUserManager):   # to manage users in the system
    """manager for users"""

    def create_user(self, email, password=None, **extra_field):
        """"create and save a new user"""

        user=self.model(email=email, **extra_field)
        user.set_password(password)
        user.save(using=self.db)




        return user





class User(AbstractBaseUser, PermissionsMixin):  # to represent a user in the system
    """user in the system"""

    email=models.EmailField(max_length=255, unique=True)
    name= models.CharField(max_length=255)
    is_active= models.BooleanField(default=True)
    is_staff= models.BooleanField(default=False)

    objects = UserManager()

    
    USERNAME_FIELD='email'
