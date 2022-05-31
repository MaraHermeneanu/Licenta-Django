from django.contrib.auth.models import User
from django.db import models
from PIL import Image


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        # img = ResizedImageField(size=[500, 300], upload_to=self.image.path, blank=True, null=True)

        # if img.height > 500 or img.width > 500:
        #     output_size = (500, 500)
        #     img.thumbnail(output_size)
        #     img.save(self.image.path)

class CameraParameters(models.Model): 
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default='')
    K = models.BinaryField()
    dist = models.BinaryField()
    # rvecs = models.CharField(max_length=200,default='')
    # tvecs = models.CharField(max_length=200,default='')
    focal_length = models.FloatField()

    class Meta: 
        constraints = [models.UniqueConstraint(fields = ['user', 'name'], name = 'unique_constraint')]

    def __str__(self):
        if "predefined" in self.name.lower():
            return self.name
        else:
            return f'{self.name} Configuration'

class StereoCameraParameters(models.Model): 
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    name = models.CharField(max_length=200, default='')
    K1 = models.BinaryField()
    D1 = models.BinaryField()
    K2 = models.BinaryField()
    D2 = models.BinaryField()
    R = models.BinaryField()
    T = models.BinaryField()
    E = models.BinaryField()
    F = models.BinaryField()
    R1 = models.BinaryField()
    P1 = models.BinaryField()
    R2 = models.BinaryField()
    P2 = models.BinaryField()
    Q = models.BinaryField()
    focal_length = models.FloatField()

    class Meta: 
        constraints = [models.UniqueConstraint(fields = ['user', 'name'], name = 'unique_constraint_stereo')]

    def __str__(self):
        if "predefined" in self.name.lower():
            return self.name
        else:
            return f'{self.name} Stereo Configuration'


class ChessboardImage(models.Model):
    image = models.ImageField(default='',upload_to='chessboard_images')
