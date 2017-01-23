from django.db import models
from django.db.models import Sum, Avg, Min, Max, StdDev, Variance, F, FloatField
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma

from dateutil.relativedelta import relativedelta

from simple_history.models import HistoricalRecords
from django_extensions.db.models import (
    TitleSlugDescriptionModel, TimeStampedModel)

from ordered_model.models import OrderedModel

#price_per_page=Sum(F('price')/F('pages'), output_field=FloatField()))

#will need to initialize codes with from ofxparse.mcc import codes
class MerchantCategoryCode(models.Model):
    mcc_id = models.IntegerField(primary_key=True)
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
        m = MerchantCategoryCode.objects.get_or_create(mcc_id = int(code))
        if m[1]:
            m[0].mcc_combined_description = codes[code].get(
                'combined description'),
            m[0].mcc_usda_description = codes[code].get('USDA description'),
            m[0].mcc_irs_description = codes[code].get('IRS Description'),
            m[0].mcc_reportable = codes[code].get(
                'Reportable under 6041/6041A and Authority for Exception')
            m[0].save()

class AccountType(models.Model):
    account_type = models.IntegerField(primary_key=True)
    description = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return '%s: %s' % (self.account_type, self.description)

class Account(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)

    number = models.CharField(max_length=255)
    routing_number = models.CharField(max_length=55)
    
    account_type = models.ForeignKey(AccountType)
    
    branch_id = models.CharField(max_length=255, blank=True)
    curdef = models.CharField(max_length=10)
    institution = models.CharField(max_length=255)

    current_balance = models.DecimalField(
        max_digits=8, decimal_places=2, null=True)
    current_balance_date = models.DateTimeField(blank=True, null=True)

    statement_start_date = models.DateTimeField(blank=True, null=True)
    statement_end_date = models.DateTimeField(blank=True, null=True)
    statement_balance = models.DecimalField(
        max_digits=8, decimal_places=2, null=True)
    statement_available_balance = models.DecimalField(
        max_digits=8, decimal_places=2, null=True)

    nickname = models.CharField(max_length=50, blank=True)

    class Meta:
        unique_together = (('owner', 'number'),)

    @property
    def formatted_statement_balance(self):
        return '%s%s' % (
            intcomma(int(self.statement_balance)), 
            ("%0.2f" % self.statement_balance)[-3:])

    @property
    def formatted_statement_available_balance(self):
        return '%s%s' % (
            intcomma(int(self.statement_balance)), 
            ("%0.2f" % self.statement_balance)[-3:])

    @property
    def formatted_current_balance(self):
        if self.current_balance:
            return '%s%s' % (
                intcomma(int(self.current_balance)), 
                ("%0.2f" % self.current_balance)[-3:])
        return '0.00'

    def __str__(self):
        return '%s %s %s %s: $%s' % (
            self.owner, 
            self.number, 
            self.nickname, 
            self.account_type.description, 
            self.formatted_current_balance)

    

class Transaction(TimeStampedModel, OrderedModel):
    account = models.ForeignKey(Account)

    date = models.DateTimeField()
    number = models.CharField(max_length=255)
    transaction_type = models.CharField(max_length=10, blank=True)

    payee = models.CharField(max_length=255, blank=True)
    memo = models.CharField(max_length=255, blank=True)
    checknum = models.IntegerField(blank=True, null=True)

    mcc = models.IntegerField(blank=True, null=True)
    sic = models.IntegerField(blank=True, null=True)

    amount = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True)

    transaction_balance = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True)

    order_with_respect_to = 'account'

    class Meta(OrderedModel.Meta):
        pass

    @property
    def formatted_amount(self):
        return '%s%s' % (
            intcomma(int(self.amount)), 
            ("%0.2f" % self.amount)[-3:])        
    
    @property
    def formatted_transaction_balance(self):
        return '%s%s' % (
            intcomma(int(self.transaction_balance)), 
            ("%0.2f" % self.transaction_balance)[-3:])

    def __str__(self):
        return '%s\t%s\t%s\t%s' % (
            self.date, self.payee, self.amount, self.transaction_balance)



class Category(TimeStampedModel):
    name = models.CharField(max_length=255)
    parent = models.ForeignKey(
        'self', blank = True, null = True, related_name = 'children')
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
    target_amount = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True)


class BudgetItem(TimeStampedModel):
    budget = models.ForeignKey(Budget)
    payee = models.ForeignKey(PayeeXref, blank=True, null=True)
    
    budget_item_date = models.DateTimeField(
        help_text='Projected date for allocation', blank=True)
    budget_item_enddate = models.DateTimeField(
        help_text='If a ranged budget item, provide an end date', blank=True)

    enforce_due_date = models.BooleanField(
        help_text='Rigid scheduling of budget item date in cashflow')

    reserve = models.ForeignKey(BudgetReserve, blank=True)
    category = models.ForeignKey(Category)

    target_amount = models.DecimalField(max_digits=8, decimal_places=2)

    notes = models.CharField(max_length=255)

    status = models.ForeignKey(BudgetItemStatus)

    def enddate_offset(self, *args, **kwargs):
        '''Pass offset_days, offset_months, and offset_years as 
        arguments to set the range end'''
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
