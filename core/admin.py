from .models import *

from django.db import transaction
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.urls import reverse
from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .utils import check_permission


class ManagerAdmin(UserAdmin):
    model = Manager
    list_display = ['username', 'contact', 'role']
    list_filter = ['role']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Личная информация', {'fields': ('contact',)}),
        ('Роли и доступы', {'fields': ('role', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role'),
        }),
    )
admin.site.register(Manager, ManagerAdmin)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    search_fields = ['name', 'phone', 'passport_series', 'passport_number']

class ProductInline(admin.TabularInline):
    model = Product
    extra = 0
    can_delete = False
    readonly_fields = ['type', 'status', 'amount', 'interest_rate', 'duration', 'open_product']

    def open_product(self, obj):
        url = reverse('admin:core_product_change', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" style="background-color: #007bff; color: white; padding: 5px 10px; text-decoration: none;">Открыть</a>',
            url
        )
    open_product.short_description = "Действия"

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    inlines = [ProductInline]
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
            return ()

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


class PaymentScheduleInline(admin.TabularInline):
    model = PaymentSchedule
    extra = 0
    fields = ['amount', 'scheduled_date', 'actual_date', 'status', 'create_transaction']
    readonly_fields = ['create_transaction']

    def create_transaction(self, obj):
        if obj.pk:
            if obj.transaction:
                return format_html('<span>Транзакция создана</span>')
            url = reverse('admin:core_transaction_add')
            params = f"?payment_schedule={obj.id}&product={obj.product.id}&client={obj.product.client.id}&amount={obj.amount}"
            return format_html(
                '<a class="button" href="{}{}">Создать транзакцию</a>',
                url,
                params
            )
        return "Сначала сохраните платеж"
    create_transaction.short_description = "Создать транзакцию"


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [PaymentScheduleInline]
    readonly_fields_on_update = ['client', 'type', 'amount', 'interest_rate', 'duration', 'created_at', 'download_schedule']

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return self.readonly_fields_on_update + list(super().get_readonly_fields(request, obj))
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

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
    list_display = ['id', 'type', 'status', 'client', 'amount', 'interest_rate', 'duration', 'created_at']
    list_filter = ['type', 'status', 'created_at']

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

    def download_schedule(self, obj):
        if obj.pk:
            return mark_safe(f"""
                <a class="button" href="{reverse('product_report', args=['pdf', obj.pk])}" style="margin-bottom: 10px;">
                    Скачать график платежей в PDF отчете</a><br><br>
                <a class="button" href="{reverse('product_report', args=['csv', obj.pk])}" style="margin-bottom: 10px;">
                Скачать график платежей в CSV таблице</a>
            """)
        return None
    download_schedule.short_description = "Сформировать отчет"

@admin.register(PaymentSchedule)
class PaymentScheduleAdmin(admin.ModelAdmin):
    search_fields = [
        'product__client__contact__name',
        'product__client__contact__phone',
        'passport_full_s',
        'passport_full',
        'product__client__contact__passport_series',
        'product__client__contact__passport_number',
        'product__client__id',
        'product__client__id',
        'product__id',
        'id',
    ]
    list_display = ['product', 'amount', 'scheduled_date', 'actual_date', 'status', 'create_transaction_button']
    list_filter = ['status', 'scheduled_date', 'actual_date']

    def get_search_results(self, request, queryset, search_term):
        if search_term:
            queryset = queryset.annotate(
                passport_full_s=Concat('product__client__contact__passport_series', Value(' '), 'product__client__contact__passport_number'),
                passport_full=Concat('product__client__contact__passport_series', 'product__client__contact__passport_number'),
            ).filter(
                Q(product__client__contact__name__icontains=search_term) |
                Q(product__client__contact__phone__icontains=search_term) |
                Q(passport_full_s__icontains=search_term) |
                Q(passport_full__icontains=search_term) |
                Q(product__client__id__icontains=search_term) |
                Q(id__icontains=search_term)
            )
        return super().get_search_results(request, queryset, search_term)

    def create_transaction_button(self, obj):
        if obj.transaction:
            return format_html('<span>Транзакция создана</span>')
        url = reverse('admin:core_transaction_add')
        return format_html(
            '<a class="button" href="{}?payment_schedule={}&client={}&product={}&amount={}">Создать транзакцию</a>',
            url, obj.id, obj.product.client.id, obj.product.id, obj.amount
        )
    create_transaction_button.short_description = "Действия"

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    readonly_fields = ['date']
    fields = ['client', 'product', 'amount', 'type', 'status']
    readonly_fields_on_update = ['client', 'product', 'amount', 'type', 'date', 'approved_status']

    def get_fields(self, request, obj=None):
        base_fields = super().get_fields(request, obj)
        return base_fields + (
            ['date', 'approved_status'] if obj and obj.pk else []
        ) + (['approve_buttons_editor'] if check_permission('approve_transaction', request.user) else [])

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return self.readonly_fields_on_update + list(super().get_readonly_fields(request, obj))
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(self, request, obj=None):
        if not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    search_fields = [
        'client__contact__name',
        'client__contact__phone',
        'passport_full_s',
        'passport_full',
        'client__id',
        'product__id',
        'id',
    ]
    list_display = ['id', 'product', 'amount', 'type', 'date', 'status', 'approved_status']
    list_filter = ['type', 'status', 'date', 'approved']

    def get_list_display(self, request, obj=None):
        return self.list_display + (['approve_buttons'] if check_permission('approve_transaction', request.user) else [])

    def approve_buttons_editor(self, obj):
        if obj and obj.pk:
            return mark_safe(self.approve_buttons(obj))
        return "Недостаточно прав"
    approve_buttons_editor.short_description = "Одобрение транзакции"

    def approved_status(self, obj):
        if obj.approved is None:
            return "Ожидает"
        return "Одобрена" if obj.approved else "Отклонена"
    approved_status.short_description = "Проверка"

    def approve_buttons(self, obj):
        if obj.approved is None:
            return format_html(
                '<a class="button" style="margin-right: 5px" href="{}">Одобрить</a><a class="button" href="{}">Отклонить</a>',
                reverse('transaction_approve', args=[obj.id]),
                reverse('transaction_reject', args=[obj.id])
            )
        return "Обработано"
    approve_buttons.short_description = ""


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

    def add_view(self, request, form_url='', extra_context=None):
        payment_schedule_id = request.GET.get('payment_schedule')
        print(payment_schedule_id)
        if payment_schedule_id:
            request.session['payment_schedule_id'] = payment_schedule_id
        return super().add_view(request, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        with transaction.atomic():
            super().save_model(request, obj, form, change)

            payment_schedule_id = request.session.pop('payment_schedule_id', None)
            if payment_schedule_id:
                try:
                    payment_schedule = PaymentSchedule.objects.get(id=payment_schedule_id)
                    payment_schedule.transaction = obj
                    payment_schedule.status = PaymentStatus.objects.get_or_create(
                        name="Просрочен" if obj.date.date() > payment_schedule.scheduled_date else "Оплачен"
                    )[0]
                    payment_schedule.save()
                except PaymentSchedule.DoesNotExist:
                    pass

admin.site.register(Role)
admin.site.register(ProductType)
admin.site.register(ProductStatus)
admin.site.register(PaymentStatus)
admin.site.register(TransactionStatus)
admin.site.register(TransactionType)

admin.site.site_header = 'МФО «Ура я банкрот»'