from django.views.generic.base import TemplateView

from budget.models import Account

class HomeView(TemplateView):

    template_name = 'index.html'

    def get_context_data(self, *args, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            context['accounts'] = Account.objects.filter(
                owner=self.request.user)
        
        return context



