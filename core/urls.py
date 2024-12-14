from django.urls import path
from django.http import HttpResponse
from core.views import download_payment_schedule_report, approve_transaction

urlpatterns = [
    path('transaction/<int:transaction_id>/approve/', lambda request, transaction_id:
        approve_transaction(request, transaction_id, True), name='transaction_approve'),
    path('transaction/<int:transaction_id>/reject/', lambda request, transaction_id:
        approve_transaction(request, transaction_id, False), name='transaction_reject'),
    path('report/<str:_type>/<int:product_id>', download_payment_schedule_report, name="product_report")
]
