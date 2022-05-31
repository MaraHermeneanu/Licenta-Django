from django.contrib import admin
from .models import Profile,CameraParameters,ChessboardImage,StereoCameraParameters

admin.site.register(Profile)
admin.site.register(CameraParameters)
admin.site.register(StereoCameraParameters)
admin.site.register(ChessboardImage)