from django.db import models
from django.db.models import Sum, Avg, Min, Max, StdDev, Variance, F, FloatField
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import intcomma

from dateutil.relativedelta import relativedelta
from recurrent import RecurringEvent
from dateutil import rrule

from simple_history.models import HistoricalRecords
from django_extensions.db.models import (
    TitleSlugDescriptionModel, TimeStampedModel)

from ordered_model.models import OrderedModel

#price_per_page=Sum(F('price')/F('pages'), output_field=FloatField()))

#will need to initialize codes with from ofxparse.mcc import codes

def dec_to_dollar_fmt(v):
    try:
        return '$%s%s' % (intcomma(int(v)), ("%0.2f" % v)[-3:])
    except:
        return ''

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
        return dec_to_dollar_fmt(self.statement_balance)

    @property
    def formatted_statement_available_balance(self):
        return dec_to_dollar_fmt(self.statement_balance)

    @property
    def formatted_current_balance(self):
        if self.current_balance:
            return dec_to_dollar_fmt(self.current_balance)
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

    payee = models.CharField(help_text="Payee entry from the Bank",
        max_length=255, blank=True)
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
        return dec_to_dollar_fmt(self.amount)     
    
    @property
    def formatted_transaction_balance(self):
        return dec_to_dollar_fmt(self.transaction_balance)

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

    def __str__(self):
        return self.name

class BudgetItemStatus(models.Model):
    message = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'budget item statuses'
        
class BudgetPayee(models.Model):
    name = models.CharField(max_length=255)
    account_site = models.URLField(
        help_text='account management site', 
        blank=True)
    account_notes = models.TextField(
        help_text='',
        blank=True)

    def __str__(self):
        return self.name

class BudgetReserve(models.Model):
    '''Target a Budget Reserve to "hold" unspent money from budget items'''
    budget = models.ForeignKey(Budget)
    
    title = models.CharField(
        help_text = 'Eg. Christmas 2017, Buick Maintenence, Tesla Fund',
        max_length=255)
    
    target_amount = models.DecimalField(
        max_digits=8, decimal_places=2, 
        blank=True, 
        null=True)


class BudgetItem(TimeStampedModel):
    budget = models.ForeignKey(Budget)
    payee = models.ForeignKey(BudgetPayee, blank=True, null=True)
    
    budget_item_date = models.DateTimeField(
        help_text='Projected date for allocation', 
        blank=True, 
        null=True)
    budget_item_enddate = models.DateTimeField(
        help_text='If a ranged budget item, provide an end date', 
        blank=True,
        null=True)

    enforce_due_date = models.BooleanField(
        help_text='Rigid scheduling of budget item date in cashflow')

    #in a cash flow, tells how much money COULD be spent on an item based
    #on the amount that has been "saved" by not allocating the full 
    #BudgetItem amount.  
    budget_reserve = models.ForeignKey(BudgetReserve,
        help_text='Specify to apply unused amounts or over-uses to a reserve',
        blank=True,
        null=True)

    category = models.ForeignKey(Category)

    target_amount = models.DecimalField(max_digits=8, decimal_places=2)

    notes = models.CharField(max_length=255, blank=True)

    status = models.ForeignKey(BudgetItemStatus, blank=True, null=True)

    class Meta:
        ordering = ('budget_item_date',)

    def __str__(self):
        return '%s\t%s\t$%s' % (
            self.budget_item_date.strftime('%Y-%m-%d'),
            self.payee, 
            self.target_amount)

    @property
    def formatted_amount(self):
        return dec_to_dollar_fmt(self.target_amount)     

    def get_future_like_items(self):
        q = BudgetItem.objects.filter(
            budget_item_date__gte = self.budget_item_date
        ).filter(
            budget = self.budget
        ).filter(
            payee = self.payee
        ).exclude(pk = self.pk)
        return q        

    def delete_future(self):
        q = self.get_future_like_items()
        q.delete()

    def update_future_target_amount(self, new_amount):
        if isinstance(new_amount, (int, float)):
            q = self.get_future_like_items()
            q.update(target_amount = new_amount) 

    def update_future_payee(self, new_payee):
        if isinstance(new_payee, (BudgetPayee)):
            q = self.get_future_like_items()
            q.update(payee = new_payee)     

    def generate_recurring(self, phrase):
        '''Takes a plain ENGLISH phrase and creates the future recurring 
        BudgetItems.  Phrase can be "every week until November" for example.
        Returns number i of BudgetItems added.
        THIS DELETES ALL EXISTING FUTURE INSTANCES FOR THE PAYEE'''

        self.delete_future()
        start_date = self.budget_item_date
        i = 1
        r = RecurringEvent(now_date = self.budget_item_date)
        r.parse(phrase)
        d = None
        if r.freq:
            rr = rrule.rrulestr(r.get_RFC_rrule())
            for rd in rr:
                d = rd.replace(hour = 0, minute = 0, second=0, microsecond=0)            
                if (d-start_date).days > 0 and (
                    (d-start_date).days < 1460 or i < 5
                ):
                    if self.budget_item_enddate:
                        delta = (
                            self.budget_item_enddate - self.budget_item_date
                        ) 
                    #print(d)                                    
                    self.budget_item_date = d
                    
                    if self.budget_item_enddate:
                        self.budget_item_enddate = d + delta
                    
                    self.pk = None
                    self.save()
                    i += 1
                if (d-start_date).days > 1460 and i > 5:
                    break
        return i



class TransactionAllocation(models.Model):
    transaction = models.ForeignKey(Transaction)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    budget_item = models.ForeignKey(BudgetItem)