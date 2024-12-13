from django.urls import path
from django.http import HttpResponse
from core.views import download_payment_schedule_report

urlpatterns = [
    path('<str:_type>/<int:product_id>', download_payment_schedule_report, name="product_report")
]
