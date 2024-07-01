"""
URL configuration for internal_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.selectSurvey, name="select"),
    path('<int:id>/language/', views.getLang, name="get_lang"),
    path('<int:id>/', views.getKey, name="get_key"),
    path('<int:id>/respond/', views.surveyResponse, name="respond"),
    path('submit/', views.submitResponse, name="submit"),
    path('create/', views.createSurvey, name="create"),
    path('login/', views.survey_login, name='survey_login'),
    path('logout/', views.survey_logout, name='survey_logout')
]
