from django.contrib import admin
from django.apps import apps

from budget.models import *

class CategoryInline(admin.TabularInline):
    model = Category
    extra = 0

class CategoryAdmin(admin.ModelAdmin):
    inlines = [CategoryInline,
    ]

    def get_queryset(self, request):
        qs = super(CategoryAdmin, self).get_queryset(request)
        return qs.filter(parent__isnull=True)

admin.site.register(Category, CategoryAdmin)

class MerchantCategoryCodeAdmin(admin.ModelAdmin):
    search_fields = ['mcc_combined_description']
    ordering = ('mcc_id',)

admin.site.register(MerchantCategoryCode, MerchantCategoryCodeAdmin)


app = apps.get_app_config('budget')
for model_name, model in app.models.items():
    if not admin.site.is_registered(model):
        admin.site.register(model)

