from datetime import date, timedelta
from core.models import Product, PaymentSchedule, PaymentStatus


def gen_payment_schedule(product: Product):
    interest_rate = ((product.interest_rate / 100) / 12) * product.duration
    if product.type.behavior == 'deposit':
        profit = (product.amount * interest_rate) / product.duration
        for month in range(1, product.duration + 1):
            PaymentSchedule.objects.create(
                product=product,
                amount=profit + (product.amount if month == product.duration else 0),
                scheduled_date=date.today() + timedelta(days=30 * month),
                status=PaymentStatus.objects.get_or_create(name="Назначен")[0]
            )

    else:
        interest_rate =+ 1
        monthly_payment = (product.amount * interest_rate) / product.duration
        for month in range(1, product.duration + 1):
            PaymentSchedule.objects.create(
                product=product,
                amount=monthly_payment,
                scheduled_date=date.today() + timedelta(days=30 * month),
                status=PaymentStatus.objects.get_or_create(name="Назначен")[0]
            )