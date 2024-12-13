from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('report/', include("core.urls")),
    path('', admin.site.urls)
]
