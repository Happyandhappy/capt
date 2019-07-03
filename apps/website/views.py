from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import FormView, TemplateView

from .forms import DismissBannerForm


class ActiveMenuItemMixin(object):

    def get_active_menu(self):
        return {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'active_menu': self.get_active_menu(),
        })

        return context


class TermsAndConditionsView(TemplateView):
    template_name = 'website/terms_and_conditions.html'


class HttpResponseNoContent(HttpResponse):
    status_code = 204


class DismissBannerView(FormView):
    form_class = DismissBannerForm
    http_method_names = ('post', 'options', )

    def form_valid(self, form):
        hidden_banners = set(self.request.session.get('hidden_banners', []))
        hidden_banners.add(form.cleaned_data['banner_name'])
        self.request.session['hidden_banners'] = list(hidden_banners)

        return HttpResponseNoContent()

    def form_invalid(self, form):
        return HttpResponseBadRequest()
