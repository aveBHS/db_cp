from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Permission


class Contact(models.Model):
    name = models.CharField(max_length=1000, verbose_name="ФИО")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адрес")
    passport_series = models.CharField(max_length=10, verbose_name="Серия паспорта")
    passport_number = models.CharField(max_length=10, verbose_name="Номер паспорта")

    class Meta:
        verbose_name = "Контактные данные"
        verbose_name_plural = "Контактные данные"

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Client(models.Model):
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Доход")
    work_place = models.CharField(max_length=255, null=True, blank=True, verbose_name="Место работы")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    gender = models.CharField(max_length=10, choices=(('M', 'Мужской'), ('F', 'Женский')), null=True, blank=True, verbose_name="Пол")
    contact = models.OneToOneField('Contact', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Контактные данные")

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        return f"{self.contact.name} ID{self.id}"


class Manager(AbstractUser):
    is_admin = models.BooleanField(default=False, verbose_name="Администратор")
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Должность")
    contact = models.OneToOneField('Contact', on_delete=models.CASCADE, null=True, blank=True, verbose_name="Контактные данные")

    groups = models.ManyToManyField('auth.Group', related_name='manager_user_set', blank=True, verbose_name="Группы")
    user_permissions = models.ManyToManyField('auth.Permission', related_name='manager_user_set_permissions', blank=True, verbose_name="Разрешения")

    class Meta:
        verbose_name = "Менеджер"
        verbose_name_plural = "Менеджеры"

    def get_role_permissions(self):
        return self.role.permissions.all() if self.role else Permission.objects.none()

    def get_user_permissions(self, obj=None):
        return super().get_user_permissions(obj) | set(self.get_role_permissions())

    def __str__(self):
        contact_name = self.contact.name if self.contact else "Без контакта"
        return f"{contact_name} ({self.username})"


class Role(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название должности")
    permissions = models.ManyToManyField(Permission, blank=True, verbose_name="Разрешения")

    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название типа продукта")
    behavior = models.CharField(
        max_length=20,
        choices=[('deposit', 'Депозит'), ('credit', 'Кредит')],
        default='credit',
        verbose_name="Поведение типа"
    )

    class Meta:
        verbose_name = "Тип банковского продукта"
        verbose_name_plural = "Типы банковских продуктов"

    def __str__(self):
        return self.name


class ProductStatus(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Статус")

    class Meta:
        verbose_name = "Статус продукта"
        verbose_name_plural = "Статусы продуктов"

    def __str__(self):
        return self.name


class Product(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    type = models.ForeignKey(ProductType, on_delete=models.CASCADE, verbose_name="Тип продукта")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма")
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Процентная ставка")
    duration = models.IntegerField(verbose_name="Срок (в месяцах)")
    status = models.ForeignKey(ProductStatus, on_delete=models.PROTECT, verbose_name="Статус", blank=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def save(self, *args, **kwargs):
        with transaction.atomic():
            is_new = self.pk is None
            super().save(*args, **kwargs)
            if is_new:
                from core.utils import gen_payment_schedule
                gen_payment_schedule(self)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

    def __str__(self):
        return f"{self.type.name if self.type else self._meta.verbose_name} ID{self.id} - {self.amount} руб на {self.duration} месяцев под {self.interest_rate}% годовых"


class PaymentStatus(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название статуса")

    class Meta:
        verbose_name = "Статус платежа"
        verbose_name_plural = "Статусы платежей"

    def __str__(self):
        return self.name


class PaymentSchedule(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма платежа")
    scheduled_date = models.DateField(verbose_name="Запланированная дата платежа")
    actual_date = models.DateField(null=True, blank=True, verbose_name="Фактическая дата платежа")
    status = models.ForeignKey(PaymentStatus, on_delete=models.SET_NULL, null=True, verbose_name="Статус платежа")
    transaction = models.OneToOneField('Transaction', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанная транзакция")

    class Meta:
        verbose_name = "График платежей"
        verbose_name_plural = "Графики платежей"

    def __str__(self):
        return f"Платеж {self.amount} руб. на {self.scheduled_date}"


class TransactionStatus(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название статуса транзакции")

    class Meta:
        verbose_name = "Статус транзакции"
        verbose_name_plural = "Статусы транзакций"

    def __str__(self):
        return self.name


class TransactionType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название типа транзакции")

    class Meta:
        verbose_name = "Тип транзакции"
        verbose_name_plural = "Типы транзакций"

    def __str__(self):
        return self.name


class Transaction(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, verbose_name="Клиент")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Продукт")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма транзакции")
    type = models.ForeignKey(TransactionType, on_delete=models.SET_NULL, null=True, verbose_name="Тип транзакции")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата транзакции")

    approved_by = models.ForeignKey(
        "Manager", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Одобрено старшим менеджером",
        related_name="approved_transactions"
    )
    approved = models.BooleanField(
        null=True,  # None = ожидает решения, True = одобрена, False = отклонена
        choices=[(None, 'Ожидает'), (True, 'Одобрена'), (False, 'Отклонена')],
        verbose_name="Одобрение"
    )

    status = models.ForeignKey(TransactionStatus, on_delete=models.SET_NULL, null=True, verbose_name="Статус транзакции")

    class Meta:
        verbose_name = "Транзакция"
        verbose_name_plural = "Транзакции"

        permissions = [("approve_transaction", "Может одобрять транзакции")]

    def __str__(self):
        return f"{self._meta.verbose_name} ID{self.id} ({self.status.name})"
