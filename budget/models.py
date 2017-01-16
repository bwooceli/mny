from django.db import models
from django.conf import settings

from dateutil.relativedelta import relativedelta

from simple_history.models import HistoricalRecords
from django_extensions.db.models import (TitleSlugDescriptionModel, TimeStampedModel)



#will need to initialize codes with from ofxparse.mcc import codes
class MerchantCategoryCode(models.Model):
    mcc_id = models.IntegerField()
    mcc_combined_description = models.TextField(max_length=255, blank=True)
    mcc_usda_description = models.TextField(max_length=255, blank=True)
    mcc_irs_description = models.TextField(max_length=255, blank=True)
    mcc_reportable = models.TextField(max_length=25, blank=True)

    class Meta:
        ordering = ['mcc_id']

    def __str__(self):
        return '%s %s' % (self.mcc_id, self.mcc_combined_description)


def mcc_init():
    from ofxparse.mcc import codes
    for code, value in codes.items():
        m = MerchantCategoryCode.objects.get_or_create(
            mcc_id = code,
            mcc_combined_description = codes[code].get('combined description'),
            mcc_usda_description = codes[code].get('USDA description'),
            mcc_irs_description = codes[code].get('IRS Description'),
            mcc_reportable = codes[code].get('Reportable under 6041/6041A and Authority for Exception')
        )


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
        #ordering = ['name']

    def __str__(self):
        n = ''
        if self.parent:
            n = self.parent.name + ' - '
        return n + self.name

class Budget(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=255)

    account = models.ForeignKey(Account)

class BudgetItemStatus(models.Model):
    message = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'budget item statuses'
        
class PayeeXref(models.Model):
    name = models.CharField(max_length=255)
    transaction = models.ManyToManyField(Transaction)

class BudgetReserve(models.Model):
    budget = models.ForeignKey(Budget)
    
    title = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)


class BudgetItem(TimeStampedModel):
    budget = models.ForeignKey(Budget)
    payee = models.ForeignKey(PayeeXref, blank=True, null=True)
    
    budget_item_date = models.DateTimeField(help_text='Projected date for allocation', blank=True)
    budget_item_enddate = models.DateTimeField(help_text='If a ranged budget item, provide an end date', blank=True)
    
    reserve = models.ForeignKey(BudgetReserve, blank=True)
    category = models.ForeignKey(Category)

    target_amount = models.DecimalField(max_digits=8, decimal_places=2)

    notes = models.CharField(max_length=255)

    status = models.ForeignKey(BudgetItemStatus)

    def enddate_offset(self, *args, **kwargs):
        '''Pass offset_days, offset_months, and offset_years as arguments to set the range end'''
        r = self.budget_item_date
        r = ( r  
            + relativedelta(days=kwargs.get('offset_days') or 0) 
            + relativedelta(months=kwargs.get('offset_months') or 0)
            + relativedelta(years=kwargs.get('offset_years') or 0) 
        )
        r.second = 0
        r.microsecond = 0
        self.budget_item_enddate = r
        self.save()
        

class TransactionAllocation(models.Model):
    transaction = models.ForeignKey(Transaction)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    budget_item = models.ForeignKey(BudgetItem)
