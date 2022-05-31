
from os import name

from application import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from users import views as user_views
from users.views import PasswordsChangeView

handler404 = 'application.views.not_found'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('register/', user_views.register, name='register'),
    path('profile/', user_views.profile, name='profile'),

    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('', include('application.urls')),

    path("password_reset/", user_views.password_reset_request, name="password_reset"),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password/password_reset_done.html'), name='password_reset_done'),
    path('password_reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="password/password_reset_confirm.html"), name='password_reset_confirm'),
    path('password_reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name="password/password_reset_complete.html"), name='password_reset_complete'),

    path('password_change/', PasswordsChangeView.as_view(template_name='password/password_change.html'), name='password_change'),
    path('password_change/done/', user_views.password_change_done, name="password_change_done"),
    
    path('login/', include('allauth.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('face_login/', user_views.face_login, name='face_login'),

    path("camera_calibration/",user_views.camera_calibration,name='camera_calibration'),
    path("stereo_calibration/",user_views.stereo_calibration,name='stereo_calibration'),

    path("camera_calibration/delete_camera_config/",user_views.delete_camera_config,name='delete_camera_config'),
    path("stereo_calibration/delete_stereo_config/",user_views.delete_stereo_config,name='delete_stereo_config'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
