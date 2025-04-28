"""
aiz_automations/filters.py
"""

from aiz.filters import aizFilterSet, django_filters
from aiz_automations.models import MailAutomation


class AutomationFilter(aizFilterSet):
    """
    AutomationFilter
    """

    search = django_filters.CharFilter(field_name="title", lookup_expr="icontains")

    class Meta:
        model = MailAutomation
        fields = "__all__"
