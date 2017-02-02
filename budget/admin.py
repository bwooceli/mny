from django.contrib import admin
from django.apps import apps

from ordered_model.admin import OrderedModelAdmin

from budget.models import *

#Transaction Admin
class TransactionAdmin(OrderedModelAdmin):
    #list_display can also have 'move_up_down_links')
    list_display = ('date', 'payee','memo', 'formatted_amount',
                    'formatted_transaction_balance', 'order')
    list_filter = ('account__nickname',)
    search_fields = ['payee']
    ordering = ('-date',)

admin.site.register(Transaction, TransactionAdmin)

#Category Admin
class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0

class CategoryAdmin(admin.ModelAdmin):
    inlines = [
        CategoryInline,
    ]

    def get_queryset(self, request):
        qs = super(CategoryAdmin, self).get_queryset(request)
        return qs.filter(parent__isnull=True)

admin.site.register(Category, CategoryAdmin)

class BudgetItemAdmin(admin.ModelAdmin):
    search_fields = ['payee__name',]
    list_display = ('budget_item_date', 'payee', 'formatted_amount')
    list_filter = ['budget__owner__username','budget__name',]

admin.site.register(BudgetItem, BudgetItemAdmin)

class BudgetItemInline(admin.TabularInline):
    model = BudgetItem
    extra = 0

class BudgetPayeeAdmin(admin.ModelAdmin):
    inlines = [
        BudgetItemInline,
    ]

admin.site.register(BudgetPayee, BudgetPayeeAdmin)

#MCC Admin
class MerchantCategoryCodeAdmin(admin.ModelAdmin):
    search_fields = ['mcc_combined_description']
    ordering = ('mcc_id',)

admin.site.register(MerchantCategoryCode, MerchantCategoryCodeAdmin)

#Generic register everything else to admin
app = apps.get_app_config('budget')
for model_name, model in app.models.items():
    if not admin.site.is_registered(model):
        admin.site.register(model)

