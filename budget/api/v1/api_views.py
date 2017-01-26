from rest_framework import viewsets

from .serializers import *

class AccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Account objects to be viewed or edited.
    """
    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    

class BudgetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Budget objects to be viewed or edited.
    """
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer  


class BudgetItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows BudgetItem objects to be viewed or edited.
    """
    queryset = BudgetItem.objects.all()
    serializer_class = BudgetItemSerializer  

class TransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Transaction objects to be viewed or edited.
    """
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer      