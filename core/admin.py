from django.db.models import Q, Value
from django.db.models.functions import Concat

from .models import *
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

class ManagerAdmin(UserAdmin):
    model = Manager
admin.site.register(Manager, ManagerAdmin)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    search_fields = ['name', 'phone', 'passport_series', 'passport_number']

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    search_fields = [
        'contact__name',
        'contact__phone',
        'contact__passport_series',
        'contact__passport_number',
        'work_place',
        'birth_date',
        'passport_full_s',
        'passport_full',
    ]

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            queryset = queryset.annotate(
                passport_full_s=Concat('contact__passport_series', Value(' '), 'contact__passport_number'),
                passport_full=Concat('contact__passport_series', 'contact__passport_number'),
            ).filter(
                Q(contact__name__icontains=search_term) |
                Q(contact__phone__icontains=search_term) |
                Q(contact__passport_series__icontains=search_term) |
                Q(contact__passport_number__icontains=search_term) |
                Q(passport_full_s__icontains=search_term) |
                Q(passport_full__icontains=search_term) |
                Q(work_place__icontains=search_term) |
                Q(birth_date__icontains=search_term)
            )
        return super().get_search_results(request, queryset, search_term)

    list_display = ['__str__', 'birth_date', 'gender', 'salary', 'work_place']

    class BirthDateRangeFilter(admin.SimpleListFilter):
        title = 'Диапазон дат рождения'
        parameter_name = 'birth_date'

        def lookups(self, request, model_admin):
            return ()  # Ничего не возвращаем, так как ввод будет ручным

        def queryset(self, request, queryset):
            start_date = request.GET.get(f'{self.parameter_name}__gte')
            end_date = request.GET.get(f'{self.parameter_name}__lte')
            if start_date and end_date:
                return queryset.filter(birth_date__range=[start_date, end_date])
            elif start_date:
                return queryset.filter(birth_date__gte=start_date)
            elif end_date:
                return queryset.filter(birth_date__lte=end_date)
            return queryset

    list_filter = ['gender', BirthDateRangeFilter]

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = [
        'id',
        'client__id',
        'client__contact__name',
        'client__contact__phone',
        'client__contact__passport_series',
        'client__contact__passport_number',
        'passport_full',
        'passport_full_s',
    ]
    list_display = ['id', 'type', 'client', 'amount', 'interest_rate', 'duration', 'created_at']
    list_filter = ['type', 'created_at']

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            queryset = queryset.annotate(
                passport_full_s=Concat('client__contact__passport_series', Value(' '), 'client__contact__passport_number'),
                passport_full=Concat('client__contact__passport_series', 'client__contact__passport_number'),
            ).filter(
                Q(client__contact__name__icontains=search_term) |
                Q(client__contact__phone__icontains=search_term) |
                Q(passport_full_s__icontains=search_term) |
                Q(passport_full__icontains=search_term) |
                Q(client__id__icontains=search_term) |
                Q(id__icontains=search_term)
            )
        return super().get_search_results(request, queryset, search_term)


@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    search_fields = [
        'client__contact__name',
        'client__contact__phone',
        'passport_full_s',
        'passport_full',
        'product__client__contact__passport_series',
        'product__client__contact__passport_number',
        'product__client__id',
        'client__id',
        'product__id',
        'id',
    ]
    list_display = ['product', 'amount', 'scheduled_date', 'actual_date', 'status']
    list_filter = ['status', 'scheduled_date', 'actual_date']

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            queryset = queryset.annotate(
                passport_full_s=Concat('client__contact__passport_series', Value(' '), 'client__contact__passport_number'),
                passport_full=Concat('client__contact__passport_series', 'client__contact__passport_number'),
            ).filter(
                Q(client__contact__name__icontains=search_term) |
                Q(client__contact__phone__icontains=search_term) |
                Q(passport_full_s__icontains=search_term) |
                Q(passport_full__icontains=search_term) |
                Q(client__id__icontains=search_term) |
                Q(id__icontains=search_term)
            )
        return super().get_search_results(request, queryset, search_term)

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    search_fields = [
        'client__contact__name',
        'client__contact__phone',
        'passport_full_s',
        'passport_full',
        'client__id',
        'product__id',
        'id',
    ]
    list_display = ['id', 'client', 'product', 'amount', 'type', 'date', 'status']
    list_filter = ['type', 'status', 'date']

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            queryset = queryset.annotate(
                passport_full_s=Concat('client__contact__passport_series', Value(' '), 'client__contact__passport_number'),
                passport_full=Concat('client__contact__passport_series', 'client__contact__passport_number'),
            ).filter(
                Q(client__contact__name__icontains=search_term) |
                Q(client__contact__phone__icontains=search_term) |
                Q(passport_full_s__icontains=search_term) |
                Q(passport_full__icontains=search_term) |
                Q(client__id__icontains=search_term) |
                Q(product__id__icontains=search_term) |
                Q(id__icontains=search_term)
            )
        return super().get_search_results(request, queryset, search_term)

admin.site.register(Role)
admin.site.register(ProductType)
admin.site.register(PaymentStatus)
admin.site.register(TransactionStatus)
admin.site.register(TransactionType)

admin.site.site_header = 'МФО «Ура я банкрот»'