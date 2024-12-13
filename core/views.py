from datetime import date
from django.http import HttpResponse

from core.models import Product
from core.utils import generate_payment_schedule_pdf


def download_payment_schedule_pdf(request, product_id: int):
    try:
        product = Product.objects.get(id=product_id)
        filename = f"tmp/ps_{product.id}_{date.today()}.pdf"
        generate_payment_schedule_pdf(product, filename)

        with open(filename, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
    except Product.DoesNotExist:
        return HttpResponse("Продукт не найден.", status=404)
