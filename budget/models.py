from django.db import models
from django.conf import settings

from simple_history.models import HistoricalRecords
from django_extensions.db.models import (TitleSlugDescriptionModel, TimeStampedModel)


class CurrencyField(models.DecimalField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, verbose_name=None, name=None, **kwargs):
        decimal_places = kwargs.pop('decimal_places', 2)
        max_digits = kwargs.pop('max_digits', 10)

        super(CurrencyField, self). __init__(
            verbose_name = verbose_name, 
            name = name, 
            max_digits = max_digits,
            decimal_places = decimal_places, 
            **kwargs
        )

    def to_python(self, value):
        try:
            return super(CurrencyField, self).to_python(value).quantize(Decimal("0.01"))
        except AttributeError:
            return None

#will need to initialize codes with from ofxparse.mcc import codes
class MerchantCategoryCode(models.Model):
    mcc_id = models.IntegerField
    mcc_combined_description = models.TextField(max_length=255, blank=True)
    mcc_usda_description = models.TextField(max_length=255, blank=True)
    mcc_irs_description = models.TextField(max_length=255, blank=True)
    mcc_reportable = models.TextField(max_length=255, blank=True)

class Account(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)

    account_id = models.CharField(max_lenght=255)
    account_type = models.CharField(max_lenght=255)
    branch_id = models.CharField(max_length=255, blank=True)
    curdef = models.CharField(max_length=10)
    institution = models.CharField(max_length=255)
    number = models.CharField(max_length=255)
    routing_number = models.CharField(max_length=55)
    acctype = models.IntegerField()

    class Meta:
        unique_together = (('owner', 'account_id'),)

class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account)

    t_tdate = models.DateTimeField()
    t_id = models.CharField(max_length=255)
    t_type = models.CharField(max_length=10, blank=True)

    t_payee = models.CharField(max_length=255)
    t_memo = models.CharField(max_length=255, blank=True)
    t_checknum = models.IntegerField(blank=True, null=True)

    t_mcc = models.IntegerField(blank=True, null=True)
    t_sic = models.IntegerField(blank=True, null=True)

    t_amount = models.CurrencyField()

    post_order = models.IntegerField()    


class Category(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', blank = True, null = True, related_name = 'children')
    mcc = models.ForeignKey(MerchantCategoryCode, blank=True, null=True)
    
class Budget(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255)

    account = models.ForeignKey(Account)

class BudgetItemStatus(models.Model):
    message = models.CharField(max_length=255)

class BudgetReserve(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField

class PayeeXref(models.Model):
    name = models.CharField(max_length=255)
    transaction = models.ManyToManyField(Transaction)

class BudgetItem(TimeStampedModel):
    budget = models.ForeignKey(Budget)
    payee = models.ForeignKey(PayeeXref, blank=True, null=True)
    budget_item_date = models.DateField(help_text='Projected date for allocation', blank=True)
    reserve = models.ForeignKey(BudgetReserve, blank=True)
    category = models.ForeignKey(Category)

    amount = CurrencyField()

    notes = models.CharField(max_length=255)

    status = models.ForeignKey(BudgetItemStatus)


class TransactionAllocation(models.Model):
    transaction = models.ForeignKey(Transaction)
    amount = models.CurrencyField()
    budget_item = models.ForeignKey(BudgetItem)
