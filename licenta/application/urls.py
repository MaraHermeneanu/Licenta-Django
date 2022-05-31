from django.urls import path
from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('projects/', views.projects, name="projects"),
    path('dashboard/search_project/', views.search_project, name="search_project"),
    path("projects/delete_project/",views.delete_project,name='delete_project'),
    path('ajax/download_ply/', views.download_ply, name="download_ply"),
    path('ajax/send_message/', views.send_message, name='send_message'),
]

