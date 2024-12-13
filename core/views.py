from datetime import date
from django.http import HttpResponse

from core.models import Product
from core.utils import generate_payment_schedule_pdf, generate_payment_schedule_csv


def download_payment_schedule_report(request, product_id: int, _type: str):
    _type = _type.lower().strip()
    action = {
        'csv': {'generate': generate_payment_schedule_csv, 'content_type': "application/pdf"},
        'pdf': {'generate': generate_payment_schedule_pdf, 'content_type': "text/csv"},
    }.get(_type)

    if action:
        try:
            product = Product.objects.get(id=product_id)
            filename = f"tmp/ps_{product.id}_{date.today()}.{_type}"
            action['generate'](product, filename)

            with open(filename, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type=action['content_type'])
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        except Product.DoesNotExist:
            return HttpResponse("Продукт не найден.", status=404)
    return HttpResponse("Некорректный формат файла.", status=400)
