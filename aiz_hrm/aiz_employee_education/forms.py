from django import forms
from django.template.loader import render_to_string

from base.forms import ModelForm
from aiz_employee_education.models import EmployeeEducation
from aiz_widgets.widgets.aiz_multi_select_field import aizMultiSelectField
from aiz_widgets.widgets.select_widgets import aizMultiSelectWidget


class EmployeeEducationForm(ModelForm):

    verbose_name = "Employee Education"

    class Meta:
        model = EmployeeEducation
        fields = "__all__"
        exclude = ["status", "is_active"]
        widgets = {
            "employee_id": forms.HiddenInput()
        }

    def as_p(self):
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class EmployeeEducationUpdateForm(ModelForm):
    """form to Update a EmployeeEducation"""

    verbose_name = "EmployeeEducation"

    class Meta:
        model = EmployeeEducation
        fields = "__all__"
        exclude = ["is_active"]

