from django.db import models
from django.conf import settings

from simple_history.models import HistoricalRecords
from django_extensions.db.models import (TitleSlugDescriptionModel, TimeStampedModel)

#will need to initialize codes with from ofxparse.mcc import codes
class MerchantCategoryCode(models.Model):
    mcc_id = models.IntegerField
    mcc_combined_description = models.TextField(max_length=255, blank=True)
    mcc_usda_description = models.TextField(max_length=255, blank=True)
    mcc_irs_description = models.TextField(max_length=255, blank=True)
    mcc_reportable = models.TextField(max_length=255, blank=True)

class Account(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)

    account_id = models.CharField(max_length=255)
    account_type = models.CharField(max_length=255)
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

    t_amount = models.DecimalField(max_digits=8, decimal_places=2)

    post_order = models.IntegerField()    


class Category(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey('self', blank = True, null = True, related_name = 'children')
    mcc = models.ForeignKey(MerchantCategoryCode, blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "categories"

class Budget(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255)

    account = models.ForeignKey(Account)

class BudgetItemStatus(models.Model):
    message = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'budget item statuses'
        
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

    amount = models.DecimalField(max_digits=8, decimal_places=2)

    notes = models.CharField(max_length=255)

    status = models.ForeignKey(BudgetItemStatus)


class TransactionAllocation(models.Model):
    transaction = models.ForeignKey(Transaction)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    budget_item = models.ForeignKey(BudgetItem)
