from rest_framework import routers

from .api_views import *

#API Routes
router = routers.DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'budgets', BudgetViewSet)

router.register(r'budget_items', BudgetViewSet)
router.register(r'transactions', TransactionViewSet)

urlpatterns = router.urls