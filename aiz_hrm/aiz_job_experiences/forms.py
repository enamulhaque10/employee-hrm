from django import forms
from django.template.loader import render_to_string

from base.forms import ModelForm
from base.methods import reload_queryset
from employee.filters import EmployeeFilter
from employee.models import Employee
from aiz_job_experiences.models import EmployeeJobExperiences
from aiz_widgets.widgets.aiz_multi_select_field import aizMultiSelectField
from aiz_widgets.widgets.select_widgets import aizMultiSelectWidget


class JobExperienceForm(ModelForm):

    verbose_name = "Employee Job Experience"

    class Meta:
        model = EmployeeJobExperiences
        fields = "__all__"
        exclude = ["status", "is_active", "title"]
        widgets = {
            "employee_id": forms.HiddenInput()
        }

    def as_p(self):
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class JobExperienceUpdateForm(ModelForm):
    """form to Update a Job Experience"""

    verbose_name = "Job Experience"

    class Meta:
        model = EmployeeJobExperiences
        fields = "__all__"
        exclude = ["is_active"]

