from django import forms
from django.template.loader import render_to_string

from base.forms import ModelForm
from base.methods import reload_queryset
from employee.filters import EmployeeFilter
from employee.models import Employee, EmployeeIncident
from aiz_documents.models import Document, DocumentRequest, DocumentCategory
from aiz_widgets.widgets.aiz_multi_select_field import aizMultiSelectField
from aiz_widgets.widgets.select_widgets import aizMultiSelectWidget


class DocumentRequestForm(ModelForm):
    """form to create a new Document Request"""

    class Meta:
        model = DocumentRequest
        fields = "__all__"
        exclude = ["is_active"]

    def clean(self):
        cleaned_data = super().clean()
        if isinstance(self.fields["employee_id"], aizMultiSelectField):
            self.errors.pop("employee_id", None)
            if len(self.data.getlist("employee_id")) < 1:
                raise forms.ValidationError({"employee_id": "This field is required"})

            employee_data = self.fields["employee_id"].queryset.filter(
                id__in=self.data.getlist("employee_id")
            )
            cleaned_data["employee_id"] = employee_data

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["employee_id"] = aizMultiSelectField(
            queryset=Employee.objects.all(),
            widget=aizMultiSelectWidget(
                filter_route_name="employee-widget-filter",
                filter_class=EmployeeFilter,
                filter_instance_contex_name="f",
                filter_template_path="employee_filters.html",
                required=True,
                instance=self.instance,
            ),
            label="Employee",
        )
        reload_queryset(self.fields)


class DocumentForm(ModelForm):
    """form to create a new Document"""

    verbose_name = "Document"

    class Meta:
        model = Document
        fields = "__all__"
        exclude = ["document_request_id", "status", "reject_reason", "is_active", "issue_date","expiry_date", "is_digital_asset"]
        widgets = {
            "employee_id": forms.HiddenInput(),
            "issue_date": forms.DateInput(
                attrs={"type": "date", "class": "oh-input  w-100"}
            ),
            "expiry_date": forms.DateInput(
                attrs={"type": "date", "class": "oh-input  w-100"}
            ),
        }

    def as_p(self):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class IncidentForm(ModelForm):

    verbose_name = "Incident"

    class Meta:
        model = EmployeeIncident
        fields = "__all__"
        exclude = [ "status", "is_active"]
        widgets = {
            "employee_id": forms.HiddenInput(),
            "issue_date": forms.DateInput(
                attrs={"type": "date", "class": "oh-input  w-100"}
            ),
        }

    def as_p(self):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class DocumentUpdateForm(ModelForm):
    """form to Update a Document"""

    verbose_name = "Document"

    class Meta:
        model = Document
        fields = "__all__"
        exclude = ["is_active"]
        widgets = {
            "issue_date": forms.DateInput(
                attrs={"type": "date", "class": "oh-input  w-100"}
            ),
            "expiry_date": forms.DateInput(
                attrs={"type": "date", "class": "oh-input  w-100"}
            ),
        }


class DocumentRejectForm(ModelForm):
    """form to add rejection reason while rejecting a Document"""

    class Meta:
        model = Document
        fields = ["reject_reason"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reject_reason"].widget.attrs["required"] = True

class DocumentCategoryForm(ModelForm):

    class Meta:
        model = DocumentCategory
        fields = ["category_title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category_title"].widget.attrs["required"] = True
