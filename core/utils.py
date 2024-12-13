import csv
import pdfkit
from jinja2 import Template
from datetime import date, timedelta

from core.settings import WKHTMLTOPDF_PATH, PRODUCT_TYPES
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
        interest_rate += 1
        monthly_payment = (product.amount * interest_rate) / product.duration
        for month in range(1, product.duration + 1):
            PaymentSchedule.objects.create(
                product=product,
                amount=monthly_payment,
                scheduled_date=date.today() + timedelta(days=30 * month),
                status=PaymentStatus.objects.get_or_create(name="Назначен")[0]
            )


def get_payment_schedule_table(product: Product):

    schedule = PaymentSchedule.objects.filter(product=product)

    data = []
    amount_paid = 0
    remaining_amount = sum([p.amount for p in schedule])
    for i, payment in enumerate(schedule):
        amount_paid += payment.amount
        current_remaining_amount = remaining_amount - amount_paid
        current_interest_amount = current_remaining_amount - product.amount
        current_main_amount = product.amount if current_interest_amount > 0 else (
                product.amount + current_interest_amount)

        data.append([
            i + 1, payment.scheduled_date, payment.amount,
            str(current_interest_amount if current_interest_amount > 0 else 0) + "₽",
            str(current_main_amount) + "₽",
            str(current_remaining_amount) + "₽"
        ])

    return {
        "table": [[
            "№", "Запланированная дата платежа", "Сумма платежа",
            "Проценты", "Основная сумма", "Общий долг"
        ], *data],
        "interest_amount": remaining_amount - product.amount
    }


def generate_payment_schedule_pdf(product: Product, filename: str):
    config = pdfkit.configuration(wkhtmltopdf=WKHTMLTOPDF_PATH)
    data = get_payment_schedule_table(product)
    pdfkit.from_string(Template(open(
        "./core/templates/core/pdf_report.html", "r", encoding="utf-8"
    ).read()).render(
        data=data['table'],
        product_id=product.id,
        client_name=product.client.contact.name,
        client_phone=product.client.contact.phone,
        product_type=PRODUCT_TYPES[product.type.behavior],
        product_amount=product.amount,
        interest_rate=product.interest_rate,
        product_duration=product.duration,
        interest_amount=data['interest_amount']
    ), filename, configuration=config)
    return filename

def generate_payment_schedule_csv(product: Product, filename: str):
    data = get_payment_schedule_table(product)
    extra_data = [
        [f"График платежей по договору №{product.id}"],
        ["Клиент", product.client.contact.name],
        ["Контактный телефон", str(product.client.contact.phone)],
        [f"Сумма {PRODUCT_TYPES[product.type.behavior]}а", f"{product.amount}₽"],
        ["Процентная ставка", f"{product.interest_rate}% годовых"],
        ["Начисления", f"{data['interest_amount']}₽</p>"],
        ["Срок договора", f"{product.duration} месяца(ев)"],
    ]

    csv_data = []
    for row in [*extra_data, *data['table']]:
        csv_data.append("\t".join([str(el) for el in row]))

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(csv_data))

    return filename
