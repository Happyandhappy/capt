from datetime import datetime, timedelta, timezone
import simplejson

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import SuspiciousOperation
from django.urls import reverse
from django.views.generic import DetailView, TemplateView, UpdateView
from django.db import connection

from accounts.views import PaidAccountRequiredMixin
from adwords.adapter import Adapter
from campaign_modifiers.models import KeywordEvent, ModifierProcessLog
from website.views import ActiveMenuItemMixin

from .forms import CampaignForm, DateRangeForm
from .models import Campaign
from .tables import (
    CampaignTable,
    KeywordTable,
    RunTable,
)


class DashboardView(
        ActiveMenuItemMixin,
        LoginRequiredMixin,
        PaidAccountRequiredMixin,
        TemplateView):
    template_name = 'reports/dashboard.html'

    def get_active_menu(self):
        date_range = self.request.GET.get('range', 'today')

        return {
            'dashboard': True,
            'dashboard_today': date_range == 'today',
            'dashboard_week': date_range == 'week',
            'dashboard_month': date_range == 'month',
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.user.has_adwords_account:
            return context

        context['has_adwords_account'] = True

        date_range_form = DateRangeForm()
        date_from = date_range_form.fields['date_from'].initial()
        date_to = date_range_form.fields['date_to'].initial()
        should_aggregate = date_range_form.fields['should_aggregate'].initial

        if 'date_from' in self.request.GET and 'date_to' in self.request.GET:
            date_range_form = DateRangeForm(self.request.GET.copy())
            if date_range_form.is_valid():
                date_from = date_range_form.cleaned_data['date_from']
                date_to = date_range_form.cleaned_data['date_to']
                should_aggregate = date_range_form.cleaned_data['should_aggregate']

        context['date_range_form'] = date_range_form
        context['chart_range'] = self.request.GET.get('chart_range', 'last30Days')

        adapter = Adapter(self.request.user)
        kwargs = {'cast_dates': False}
        if context['chart_range'] != 'allTime':
            kwargs['date_range'] = adapter.format_date_range(date_from, date_to)

        metrics = adapter.get_campaign_metrics(**kwargs)

        if should_aggregate:
            metrics = adapter.aggregate_campaign_metrics_to_monthly(
                metrics, date_format='%Y-%m-%d')

        for metric in metrics.values():
            metric['cpc'] /= 10**6
        context['metrics'] = simplejson.dumps(metrics)

        event_date_range = self.request.GET.get('range', 'today').lower()
        date_range_lengths = {'today': 1, 'week': 7, 'month': 28}

        with connection.cursor() as cursor:
            cursor.execute("SELECT campaign_modifiers_keywordevent.action, COUNT(*) FROM campaign_modifiers_keywordevent INNER JOIN campaign_modifiers_modifierprocesslog ON campaign_modifiers_keywordevent.modifier_process_log_id=campaign_modifiers_modifierprocesslog.id INNER JOIN reports_campaign ON campaign_modifiers_modifierprocesslog.adwords_campaign_id=reports_campaign.adwords_campaign_id WHERE reports_campaign.owner_id = %s AND campaign_modifiers_keywordevent.created_at BETWEEN NOW() - INTERVAL %s DAY AND NOW() GROUP BY captivise.campaign_modifiers_keywordevent.action;", [self.request.user.id, date_range_lengths[event_date_range]])
            events = cursor.fetchall()

        increased = 0
        decreased = 0
        unchanged = 0
        paused = 0

        for event in events:
            if event[0] == "increased_cpc":
                increased = event[1]
            if event[0] == "decreased_cpc":
                decreased = event[1]
            if event[0] == "no_action":
                unchanged = event[1]
            if event[0] == "paused":
                paused = event[1]

        context.update({
            'increased_bid_count': increased,
            'decreased_bid_count': decreased,
            'unchanged_bid_count': unchanged,
            'paused_keywords_count': paused,
        })

        return context


class CampaignListView(
        ActiveMenuItemMixin,
        LoginRequiredMixin,
        PaidAccountRequiredMixin,
        TemplateView):
    template_name = 'reports/campaign/list.html'

    def get_active_menu(self):
        filter_by = self.request.GET.get('filter', 'all')
        return {
            'campaigns': True,
            'campaigns_filter_all': filter_by == 'all',
            'campaigns_filter_managed': filter_by == 'managed',
            'campaigns_filter_unmanaged': filter_by == 'unmanaged',
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.user.has_adwords_account:
            return context

        context['has_adwords_account'] = True

        adapter = Adapter(self.request.user)

        filter_by = self.request.GET.get('filter', None)
        order_by = self.request.GET.get('sort', 'title')
        try:
            page = int(self.request.GET.get('page', 1))
        except ValueError:
            # raise a 400
            raise SuspiciousOperation('Bad request:  GET parameter `page` is not an integer')

        data = adapter.get_mapped_campaigns(filter_by=filter_by)

        table = CampaignTable(data, order_by=order_by)
        table.paginate(page=page, per_page=20)

        context.update({
            'campaigns': table,
        })

        return context


class BaseCampaignView(
        ActiveMenuItemMixin,
        LoginRequiredMixin,
        PaidAccountRequiredMixin,
        DetailView):
    model = Campaign
    pk_url_kwarg = 'campaign_id'
    context_object_name = 'campaign'

    def get_active_menu(self):
        return {
            'campaigns': True,
        }


class CampaignSettingsView(UpdateView, BaseCampaignView):
    template_name = 'reports/campaign/settings.html'
    form_class = CampaignForm

    def get_active_menu(self):
        active = super().get_active_menu()

        active.update({
            'campaign_settings': True,
        })

        return active

    def get_success_url(self):
        return reverse('reports_campaign_detail', args=(self.kwargs['campaign_id'], ))


class BaseCampaignDetailView(BaseCampaignView):

    def get_active_menu(self):
        active = super().get_active_menu()

        active.update({
            'campaign_overview': True,
        })

        return active

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.user.has_adwords_account:
            return context

        context['has_adwords_account'] = True

        date_range_form = DateRangeForm()
        date_from = date_range_form.fields['date_from'].initial()
        date_to = date_range_form.fields['date_to'].initial()
        should_aggregate = date_range_form.fields['should_aggregate'].initial

        if 'date_from' in self.request.GET and 'date_to' in self.request.GET:
            date_range_form = DateRangeForm(self.request.GET.copy())
            if date_range_form.is_valid():
                date_from = date_range_form.cleaned_data['date_from']
                date_to = date_range_form.cleaned_data['date_to']
                should_aggregate = date_range_form.cleaned_data['should_aggregate']

        context['date_range_form'] = date_range_form
        context['chart_range'] = self.request.GET.get('chart_range', 'thisWeek')

        adapter = Adapter(self.request.user)
        kwargs = {'cast_dates': False, 'campaign_id': self.object.adwords_campaign_id}
        if context['chart_range'] != 'allTime':
            kwargs['date_range'] = adapter.format_date_range(date_from, date_to)

        metrics = adapter.get_campaign_metrics(**kwargs)

        if should_aggregate:
            metrics = adapter.aggregate_campaign_metrics_to_monthly(
                metrics, date_format='%Y-%m-%d')

        for metric in metrics.values():
            metric['cpc'] /= 10**6

        context['metrics'] = simplejson.dumps(metrics)

        return context


class CampaignKeywordView(BaseCampaignDetailView):
    template_name = 'reports/campaign/keywords.html'

    def get_active_menu(self):
        active = super().get_active_menu()

        active.update({
            'campaign_keywords': True,
        })

        return active

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if not self.request.user.has_adwords_account:
            return context

        context['has_adwords_account'] = True

        adapter = Adapter(self.request.user)

        data = adapter.get_mapped_keywords(self.object)

        order_by = self.request.GET.get('sort', 'keyword')
        try:
            page = int(self.request.GET.get('page', 1))
        except ValueError:
            # raise a 400
            raise SuspiciousOperation('Bad request:  GET parameter `page` is not an integer')

        table = KeywordTable(data, order_by=order_by)
        table.paginate(page=page, per_page=20)

        context.update({
            'keywords': table,
        })

        return context


class CampaignRunsView(BaseCampaignDetailView):
    template_name = 'reports/campaign/runs.html'

    def get_active_menu(self):
        active = super().get_active_menu()

        active.update({
            'campaign_runs': True,
        })

        return active

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        runs = ModifierProcessLog.objects \
            .filter(adwords_campaign_id=self.object.adwords_campaign_id) \
            .order_by('-started_at') \
            .prefetch_related('keyword_events')

        data = []
        for run in runs:
            increased = run.keyword_events.filter(
                action=KeywordEvent.ACTION_CHOICES.increased_cpc).count()
            decreased = run.keyword_events.filter(
                action=KeywordEvent.ACTION_CHOICES.decreased_cpc).count()
            unchanged = run.keyword_events.filter(
                action=KeywordEvent.ACTION_CHOICES.no_action).count()
            paused = run.keyword_events.filter(action=KeywordEvent.ACTION_CHOICES.paused).count()

            data.append({
                'created_at': run.started_at,
                'cycle_period': run.parameters.get('cycle_period', None),
                'bid_increase_count': increased,
                'bid_decrease_count': decreased,
                'no_change_count': unchanged,
                'paused_count': paused,
                'total_keyword_count': sum((increased, decreased, unchanged, paused)),
            })

        order_by = self.request.GET.get('sort', '-created_at')
        page = self.request.GET.get('page', 1)

        table = RunTable(data, order_by=order_by)
        table.paginate(page=page, per_page=20)

        context.update({
            'runs': table,
        })

        return context
