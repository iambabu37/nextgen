from django.urls import path ,include
from . import views

urlpatterns = [
    path('',views.trimmomatic,name = "trimmomatic"),
]
