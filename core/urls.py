from django.urls import path
from django.http import HttpResponse
from core.views import download_payment_schedule_pdf

urlpatterns = [
    path('pdf/<int:product_id>', download_payment_schedule_pdf, name="product_pdf_report"),
    path('csv/<int:product_id>', download_payment_schedule_pdf, name="product_csv_report")
]
