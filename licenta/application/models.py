from operator import mod
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ImagePair(models.Model):
    left_image = models.ImageField(default='', upload_to='image_pairs')
    right_image = models.ImageField(default='', upload_to='image_pairs')

class Project(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=200,default='')
    file = models.FileField(upload_to="ply_models", blank=True)
    date = models.DateTimeField(default=timezone.now)
    disparity = models.ImageField(upload_to='disparity_pics', blank=True)
    private = models.BooleanField(default=False)

    class Meta: 
        constraints = [models.UniqueConstraint(fields = ['user', 'name'], name = 'unique_constraint_project')]

    def __str__(self):
        return self.name
