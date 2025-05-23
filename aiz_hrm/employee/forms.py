"""
forms.py

This module contains the form classes used in the application.

Each form represents a specific functionality or data input in the
application. They are responsible for validating
and processing user input data.

Classes:
- YourForm: Represents a form for handling specific data input.

Usage:
from django import forms

class YourForm(forms.Form):
    field_name = forms.CharField()

    def clean_field_name(self):
        # Custom validation logic goes here
        pass
"""

import logging
import re
from datetime import date
from typing import Any

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from django.forms import DateInput, TextInput
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as trans

from base.methods import eval_validate, reload_queryset
from employee.models import (
    Actiontype,
    BonusPoint,
    DisciplinaryAction,
    Employee,
    EmployeeBankDetails,
    EmployeeGeneralSetting,
    EmployeeNote,
    EmployeeTag,
    EmployeeWorkInformation,
    NoteFiles,
    Policy,
    PolicyMultipleFile,
    EmployeeIncident,
    EventCalender
)
from aiz import aiz_middlewares
from aiz_audit.models import AccountBlockUnblock

logger = logging.getLogger(__name__)


class ModelForm(forms.ModelForm):
    """
    Overriding django default model form to apply some styles
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = getattr(aiz_middlewares._thread_locals, "request", None)
        reload_queryset(self.fields)
        for _, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.DateInput)):
                field.initial = date.today()

            if isinstance(
                widget,
                (forms.NumberInput, forms.EmailInput, forms.TextInput, forms.FileInput),
            ):
                label = trans(field.label.title())
                field.widget.attrs.update(
                    {"class": "oh-input w-100", "placeholder": label}
                )
            elif isinstance(widget, (forms.Select,)):
                label = ""
                if field.label is not None:
                    label = trans(field.label)
                field.empty_label = trans("---Choose {label}---").format(label=label)
                field.widget.attrs.update(
                    {"class": "oh-select oh-select-2 select2-hidden-accessible"}
                )
            elif isinstance(widget, (forms.Textarea)):
                if field.label is not None:
                    label = trans(field.label)
                field.widget.attrs.update(
                    {
                        "class": "oh-input w-100",
                        "placeholder": label,
                        "rows": 2,
                        "cols": 40,
                    }
                )
            elif isinstance(
                widget,
                (
                    forms.CheckboxInput,
                    forms.CheckboxSelectMultiple,
                ),
            ):
                field.widget.attrs.update({"class": "oh-switch__checkbox"})

            try:
                if self._meta.model.__name__ not in ["DisciplinaryAction"]:
                    self.fields["employee_id"].initial = request.user.employee_get
            except:
                pass

            try:
                self.fields["company_id"].initial = (
                    request.user.employee_get.get_company
                )
            except:
                pass


class UserForm(ModelForm):
    """
    Form for User model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        fields = ("groups",)
        model = User


class UserPermissionForm(ModelForm):
    """
    Form for User model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        fields = ("groups", "user_permissions")
        model = User


class EmployeeForm(ModelForm):
    """
    Form for Employee model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = Employee
        fields = "__all__"
        # fields = (
        #     "badge_id",
        #     "employee_first_name",
        #     "employee_last_name",
        #     "dob",
        #     "phone",
        #     "emergency_contact",
        #     "email",
        #     "gender",
        #     "employee_blood_group",
        #     "employee_religion",
        #     "employee_father_name",
        #     "employee_mother_name",
        #     "marital_status",
        #     "employee_spouse_name",
        #     "employee_number_of_son",
        #     "employee_number_of_daughter",
        #     "employee_nominee_name",
        #     "employee_nominee_contact",
        #     "employee_nominee_relation",
        #     "address",
        #     "employee_permanent_address",
        #     "state",
        #     "employee_nationality",
        #     "employee_nid_number",
        #     "employee_passport_number",
        #     "employee_driving_license_number",
        # )
        # labels = {
        #     "badge_id" : "Employee ID",
        #     "dob" : "Employee Date of Birth",
        #     "phone" : "Employee Contact Number",
        #     "emergency_contact" : "Emergency Contact Number",
        #     "email" : "Employee Email (Personal)",
        #     "gender" : "Employee Gender",
        #     "employee_blood_group" : "Employee Blood Group",
        #     "employee_religion" : "Employee Religion",
        #     "employee_father_name" : "Employee Father's Name",
        #     "employee_mother_name" : "Employee Mother's Name",
        #     "marital_status" : "Employee Marital Status",
        #     "employee_spouse_name" : "Employee Spouse Name",
        #     "employee_number_of_son" : "Number of Son of Employee",
        #     "employee_number_of_daughter" : "Number of Daughter of Employee",
        #     "address" : "Employee Present Address",
        #     "employee_permanent_address" : "Employee Permanent Address",
        #     "state" : "Employee Home District",
        #     "employee_nationality" : "Employee Nationality",
        #     "employee_nid_number" : "Employee NID Number",
        #     "employee_passport_number" : "Employee Passport Number",
        #     "employee_driving_license_number" : "Employee Driving License Number",
        # }
        exclude = (
            "qualification",
            "experience",
            "children",
            "emergency_contact_name",
            "emergency_contact_relation",
            "employee_user_id",
            "additional_info",
            "is_from_onboarding",
            "is_directly_converted",
            "is_active",
        )
        widgets = {
            "dob": TextInput(attrs={"type": "date", "id": "dob"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["autocomplete"] = "email"
        self.fields["phone"].widget.attrs["autocomplete"] = "phone"
        self.fields["address"].widget.attrs["autocomplete"] = "address"


        if instance := kwargs.get("instance"):
            # ----
            # django forms not showing value inside the date, time html element.
            # so here overriding default forms instance method to set initial value
            # ----
            initial = {}
            if instance.dob is not None:
                initial["dob"] = instance.dob.strftime("%H:%M")
            kwargs["initial"] = initial
        else:
            self.initial = {"badge_id": self.get_next_badge_id()}

    def as_p(self, *args, **kwargs):
        context = {"form": self}
        return render_to_string("employee/create_form/personal_info_as_p.html", context)

    def get_next_badge_id(self):
        """
        This method is used to generate badge id
        """
        from base.context_processors import get_initial_prefix
        from employee.methods.methods import get_ordered_badge_ids

        prefix = get_initial_prefix(None)["get_initial_prefix"]
        data = get_ordered_badge_ids()
        result = []
        try:
            for sublist in data:
                for item in sublist:
                    if isinstance(item, str) and item.lower().startswith(
                        prefix.lower()
                    ):
                        # Find the index of the item in the sublist
                        index = sublist.index(item)
                        # Check if there is a next item in the sublist
                        if index + 1 < len(sublist):
                            result = sublist[index + 1]
                            result = re.findall(r"[a-zA-Z]+|\d+|[^a-zA-Z\d\s]", result)

            if result:
                prefix = []
                incremented = False
                for item in reversed(result):
                    total_letters = len(item)
                    total_zero_leads = 0
                    for letter in item:
                        if letter == "0":
                            total_zero_leads = total_zero_leads + 1
                            continue
                        break

                    if total_zero_leads:
                        item = item[total_zero_leads:]
                    if isinstance(item, list):
                        item = item[-1]
                    if not incremented and isinstance(eval_validate(str(item)), int):
                        item = int(item) + 1
                        incremented = True
                    if isinstance(item, int):
                        item = "{:0{}d}".format(item, total_letters)
                    prefix.insert(0, str(item))
                prefix = "".join(prefix)
        except Exception as e:
            logger.exception(e)
            prefix = get_initial_prefix(None)["get_initial_prefix"]
        return prefix

    def clean_badge_id(self):
        """
        This method is used to clean the badge id
        """
        badge_id = self.cleaned_data["badge_id"]
        if badge_id:
            all_employees = Employee.objects.get_all()
            queryset = all_employees.filter(badge_id=badge_id).exclude(
                pk=self.instance.pk if self.instance else None
            )
            if queryset.exists():
                raise forms.ValidationError(trans("Badge ID must be unique."))
            if not re.search(r"\d", badge_id):
                raise forms.ValidationError(
                    trans("Badge ID must contain at least one digit.")
                )
        return badge_id


class EmployeeWorkInformationForm(ModelForm):
    """
    Form for EmployeeWorkInformation model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = EmployeeWorkInformation
        fields = (
            "department_id",
            "job_position_id",
            "employee_section_id",
            "employee_unit_id",
            "employee_grade",
            "reporting_manager_id",
            "employee_type_id",
            "date_joining",
            "last_promotion_date",
            "service_length_in_incepta",
            "mobile",
            "email",
            "casual_employee",
            "casual_id",
            "casual_employee_joining_date",
            "casual_employee_payroll_joining_date"
            
        )
        labels = {
            "badge_id" : "Employee ID",
        }
        exclude = ("employee_id", "company_id", "tags")

        widgets = { 
            "date_joining": DateInput(attrs={"type": "date"}),
            "last_promotion_date": DateInput(attrs={"type": "date"}),
            "contract_end_date": DateInput(attrs={"type": "date"}),
            "casual_employee_joining_date": DateInput(attrs={"type": "date"}),
            "casual_employee_payroll_joining_date": DateInput(attrs={"type": "date"}),
            
        }

    def __init__(self, *args, disable=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["autocomplete"] = "email"

        self.fields["job_position_id"].widget.attrs.update(
            {
                "onchange": "jobChange($(this))",
            }
        )
        # self.fields["casual_id"].widget.attrs.update({"id": "id_casual_id"})
        # self.fields["casual_employee_joining_date"].widget.attrs.update({"id": "id_casual_employee_joining_date"})
        # self.fields["casual_employee_payroll_joining_date"].widget.attrs.update({"id": "id_casual_employee_payroll_joining_date"})
        # self.fields["casual_employee"].widget.attrs.update({"id": "id_casual_employee"})


        for field in self.fields:
            self.fields[field].widget.attrs["placeholder"] = self.fields[field].label
            if disable:
                self.fields[field].disabled = True
        field_names = {
            "Department": "department",
            "Job Position": "job_position",
            "Employee Section": "employee_section",
            "Job Role": "job_role",
            "Employee Unit": "employee_unit",
            "Employee Grade": "work_type",
            "Employee Category": "employee_type",
            "Shift": "employee_shift",
            "Joining Date":"joining_date",
            "Offical contact":"mobile",
            "Offical Email": "email",
            "Casual Employee": "casual_employee",
            "Casual Id":"casual_id",
            "Casual Employee Joining Date":"casual_employee_joining_date",
            "Casual Employee Payroll Date":"casual_employee_payroll_joining_date"
        }
        urls = {
            "Department": "#dynamicDept",
            "Job Position": "#dynamicJobPosition",
            "Employee Section": "#dynamicEmployeeSection",
            "Job Role": "#dynamicJobRole",
            "Employee Unit": "#dynamicEmployeeUnit",
            "Employee Grade": "#dynamicWorkType",
            "Employee Category": "#dynamicEmployeeType",
            "Shift": "#dynamicShift",
            "Joining Date": "#dynamicJoining",
            "Service Length": "#dynamicServiceLength"
        }

        for label, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField) and field.label in field_names:
                if field.label is not None:
                    field_name = field_names.get(field.label)
                    if field.queryset.model != Employee and field_name:
                        translated_label = _(field.label)
                        empty_label = _("---Choose {label}---").format(
                            label=translated_label
                        )
                        self.fields[label] = forms.ChoiceField(
                            choices=[("", empty_label)]
                            + list(field.queryset.values_list("id", f"{field_name}")),
                            required=field.required,
                            label=translated_label,
                            initial=field.initial,
                            widget=forms.Select(
                                attrs={
                                    "class": "oh-select oh-select-2 select2-hidden-accessible",
                                    "onchange": f'onDynamicCreate(this.value,"{urls.get(field.label)}");',
                                }
                            ),
                        )
                        self.fields[label].choices += [
                            ("create", _("Create New {} ").format(translated_label))
                        ]

    def clean(self):
        cleaned_data = super().clean()
        if "employee_id" in self.errors:
            del self.errors["employee_id"]
        return cleaned_data

    def as_p(self, *args, **kwargs):
        context = {"form": self}
        return render_to_string("employee/create_form/personal_info_as_p.html", context)


class EmployeeWorkInformationUpdateForm(ModelForm):
    """
    Form for EmployeeWorkInformation model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = EmployeeWorkInformation
        fields = "__all__"
        exclude = ("employee_id",)

        widgets = { 
            "date_joining": DateInput(attrs={"type": "date"}),
            "last_promotion_date": DateInput(attrs={"type": "date"}),
            "contract_end_date": DateInput(attrs={"type": "date"}),
        }

    def as_p(self, *args, **kwargs):
        context = {"form": self}
        return render_to_string("employee/create_form/personal_info_as_p.html", context)


class EmployeeBankDetailsForm(ModelForm):
    """
    Form for EmployeeBankDetails model
    """

    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2, "cols": 40}))

    class Meta:
        """
        Meta class to add the additional info
        """

        model = EmployeeBankDetails
        fields = (
            "bank_name",
            "account_number",
            "branch",
            "any_other_code1",
            "address",
            "country",
            "state",
            "city",
            "any_other_code2",
        )
        exclude = ["employee_id", "is_active", "additional_info"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["address"].widget.attrs["autocomplete"] = "address"
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "oh-input w-100"

    def as_p(self, *args, **kwargs):
        context = {"form": self}
        return render_to_string("employee/update_form/bank_info_as_p.html", context)


class EmployeeBankDetailsUpdateForm(ModelForm):
    """
    Form for EmployeeBankDetails model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = EmployeeBankDetails
        fields = "__all__"
        exclude = ["employee_id", "is_active", "additional_info"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "oh-input w-100"
        for field in self.fields:
            self.fields[field].widget.attrs["placeholder"] = self.fields[field].label

    def as_p(self, *args, **kwargs):
        context = {"form": self}
        return render_to_string("employee/update_form/bank_info_as_p.html", context)


excel_columns = [
    ("badge_id", trans("Employee ID")),
    ("employee_first_name", trans("First Name")),
    ("employee_last_name", trans("Last Name")),
    ("employee_work_info__job_position_id", trans("Job Position")),
    ("employee_work_info__work_type_id", trans("Employee Grade")),
    ("employee_work_info__department_id", trans("Department")),
    ("employee_work_info__employee_section_id", trans("Employee Section")),
    ("employee_work_info__reporting_manager_id", trans("Reporting Manager")),
    ("employee_work_info__employee_unit_id", trans("Employee Unit")),
    ("employee_work_info__employee_type_id", trans("Employee Category")),
    ("employee_work_info__date_joining", trans("Date Of Joining")),
    ("employee_work_info__last_promotion_date", trans("Last Promotion Date")),
    ("employee_work_info__casual_id", trans("Casual ID for Casual Employee")),
    ("employee_casual_joining_date", trans("Joining date for Casual Employee")),
    ("employee_payroll_joining_date", trans("Payroll Enrollment date for Casual Employee")),
    ("employee_work_info__service_length_in_incepta", trans("Service Length In Incepta")),
    ("dob", trans("Date of Birth")),
    ("employee_job_experience_1", trans("Job Experience 1")),
    ("employee_job_experience_2", trans("Job Experience 2")),
    ("employee_job_experience_3", trans("Job Experience 3")),
    ("employee_job_experience_4", trans("Job Experience 4")),
    ("employee_graduation_subject", trans("Graduation Subject")),
    ("employee_graduation_university", trans("Graduation University")),
    ("employee_post_graduation_subject", trans("Post Graduation Subject")),
    ("employee_post_graduation_university", trans("Post Graduation University")),
    ("employee_highest_educational_degree", trans("Highest Educational Degree")),
    ("employee_training", trans("Professional Degree or Specialized Training")),
    ("employee_job_reference", trans("Job Reference")),
    ("employee_work_info__mobile", trans("Employee Contact Number (Official)")),
    ("employee_phone", trans("Employee Contact Number (Personal)")),
    ("emergency_contact", trans("Emergency Contact Number")),
    ("employee_work_email", trans("Employee Email(Official)")),
    ("employee_email", trans("Employee Email(Personal)")),
    ("employee_gender", trans("Employee Gender")),
    ("employee_blood_group", trans("Employee Blood Group")),
    ("employee_religion", trans("Employee Religion")),
    ("employee_father_name", trans("Employee Father's Name (According to NID)")),
    ("employee_mother_name", trans("Employee Mother's Name (According to NID)")),
    ("marital_status", trans("Employee Marital Status")),
    ("employee_spouse_name", trans("Employee Spouse Name (According to NID)_If Married")),
    ("employee_number_of_son", trans("Number of Son of Employee")),
    ("employee_number_of_daughter", trans("Number of Daughter of Employee")),
    ("employee_nominee", trans("Nominee Information")),
    ("employee_present_address", trans("Employee Present Address")),
    ("employee_permanent_address", trans("Employee Permanent Address")),
    ("employee_home_district", trans("Employee Home District")),
    ("employee_nationality", trans("Employee Nationality")),
    ("employee_nid_number", trans("Employee NID Number")),
    ("employee_passport_number", trans("Employee Passport Number(If Any)")),
    ("employee_driving_license_number", trans("Employee Driving License Number(If Any)")),
    # ("employee_photo", trans("Employee Updated Photo")),
    # ("employee_signature", trans("Employee Scanned Signature")),
    








    
    # ("phone", trans("Phone")),
    # ("experience", trans("Experience")),
    # ("country", trans("Country")),
    # ("state", trans("State")),
    # ("city", trans("City")),
    # ("address", trans("Address")),
    # ("zip", trans("Zip Code")),
    # ("marital_status", trans("Marital Status")),
    # ("children", trans("Children")),
    # ("is_active", trans("Is active")),
  
    # ("emergency_contact_name", trans("Emergency Contact Name")),
    # ("emergency_contact_relation", trans("Emergency Contact Relation")),
    
    # ("employee_work_info__mobile", trans("Work Phone")),
    # ("employee_work_info__job_role_id", trans("Job Role")),
    # ("employee_work_info__shift_id", trans("Shift")),
    # ("employee_work_info__location", trans("Work Location")),
    # ("employee_work_info__company_id", trans("Company")),
    # ("employee_bank_details__bank_name", trans("Bank Name")),
    # ("employee_bank_details__branch", trans("Branch")),
    # ("employee_bank_details__account_number", trans("Account Number")),
    # ("employee_bank_details__any_other_code1", trans("Bank Code #1")),
    # ("employee_bank_details__any_other_code2", trans("Bank Code #2")),
    # ("employee_bank_details__country", trans("Bank Country")),
    # ("employee_bank_details__state", trans("Bank State")),
    
    
    
    # ("employee_nominee_name", trans("Nominee Name")),
    # ("employee_nominee_contact", trans("Nominee Contact")),
    # ("employee_nominee_relation", trans("Nominee Relation")),




]
fields_to_remove = [
    "badge_id",
    "employee_first_name",
    "employee_last_name",
    "is_active",
    "email",
    "phone",
    "employee_bank_details__account_number",
]


class EmployeeExportExcelForm(forms.Form):
    selected_fields = forms.MultipleChoiceField(
        choices=excel_columns,
        widget=forms.CheckboxSelectMultiple,
        initial=[
            "badge_id",
            "employee_first_name",
            "employee_last_name",
            "dob",
            "employee_email",
            "employee_phone",
            "employee_gender",
            "employee_blood_group",
            "employee_home_district",
            "employee_work_info__department_id",
            "employee_work_info__job_position_id",
            "employee_work_info__job_role_id",
            "employee_work_info__employee_section_id",
            "employee_work_info__employee_unit_id",
            "employee_work_info__work_type_id",
            "employee_work_info__reporting_manager_id",
            "employee_work_info__employee_type_id",
            "experience",
            "employee_work_info__company_id",
            "employee_work_info__date_joining",
            "employee_work_info__last_promotion_date",
            "employee_work_info__service_length_in_incepta",
            "employee_work_info__employee_grade",
            "employee_job_experience_1",
            "employee_job_experience_2",
            "employee_job_experience_3",
            "employee_job_experience_4",
            "employee_graduation_subject",
            "employee_graduation_university",
            "employee_post_graduation_subject",
            "employee_post_graduation_university",
            "employee_highest_educational_degree",
            "employee_training",
            "employee_job_reference",
            "emergency_contact"
            "employee_work_email",
            "employee_religion",
            "employee_father_name",
            "employee_mother_name",
            "employee_marital_status",
            "employee_work_info__mobile",
            "marital_status",
            "employee_spouse_name",
            "emergency_contact_name",
            "emergency_contact_relation",
            "employee_number_of_son",
            "employee_number_of_daughter",
            "employee_present_address",
            "employee_permanent_address",
            "employee_nominee",
            "employee_nid_number",
            "employee_passport_number",
            "employee_driving_license_number",
            "employee_nationality",
            # "employee_photo",
            # "employee_signature",
            "employee_nominee_name",
            "employee_nominee_contact",
            "employee_nominee_relation"
            "employee_work_info__casual_id",
            "employee_casual_joining_date",
            "employee_payroll_joining_date"

            
        ],
    )


class BulkUpdateFieldForm(forms.Form):
    update_fields = forms.MultipleChoiceField(
        choices=excel_columns, label=_("Select Fields to Update")
    )
    bulk_employee_ids = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        updated_choices = [
            (value, label)
            for value, label in self.fields["update_fields"].choices
            if value not in fields_to_remove
        ]
        self.fields["update_fields"].choices = updated_choices
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = (
                "oh-select oh-select-2 select2-hidden-accessible oh-input w-100"
            )


class EmployeeNoteForm(ModelForm):
    """
    Form for EmployeeNote model
    """

    class Meta:
        """
        Meta class to add the additional info
        """

        model = EmployeeNote
        fields = ("description",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["note_files"] = MultipleFileField(label="files")
        self.fields["note_files"].required = False

    def save(self, commit: bool = ...) -> Any:
        attachement = []
        multiple_attachment_ids = []
        attachements = None
        if self.files.getlist("note_files"):
            attachements = self.files.getlist("note_files")
            self.instance.attachement = attachements[0]
            multiple_attachment_ids = []

            for attachement in attachements:
                file_instance = NoteFiles()
                file_instance.files = attachement
                file_instance.save()
                multiple_attachment_ids.append(file_instance.pk)
        instance = super().save(commit)
        if commit:
            instance.note_files.add(*multiple_attachment_ids)
        return instance, multiple_attachment_ids


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        if len(result) == 0:
            result = [[]]
        return result[0]


class PolicyForm(ModelForm):
    """
    PolicyForm
    """

    class Meta:
        model = Policy
        fields = "__all__"
        exclude = ["attachments", "is_active"]
        widgets = {
            "body": forms.Textarea(
                attrs={"data-summernote": "", "style": "display:none;"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["attachment"] = MultipleFileField(
            label="Attachements", required=False
        )

    def save(self, *args, commit=True, **kwargs):
        attachemnt = []
        multiple_attachment_ids = []
        attachemnts = None
        if self.files.getlist("attachment"):
            attachemnts = self.files.getlist("attachment")
            multiple_attachment_ids = []
            for attachemnt in attachemnts:
                file_instance = PolicyMultipleFile()
                file_instance.attachment = attachemnt
                file_instance.save()
                multiple_attachment_ids.append(file_instance.pk)
        instance = super().save(commit)
        if commit:
            instance.attachments.add(*multiple_attachment_ids)
        return instance, attachemnts


class BonusPointAddForm(ModelForm):
    class Meta:
        model = BonusPoint
        fields = ["points", "reason"]
        widgets = {
            "reason": forms.TextInput(attrs={"required": "required"}),
        }


class BonusPointRedeemForm(ModelForm):
    class Meta:
        model = BonusPoint
        fields = ["points"]

    def clean(self):
        cleaned_data = super().clean()
        available_points = BonusPoint.objects.filter(
            employee_id=self.instance.employee_id
        ).first()
        if available_points.points < cleaned_data["points"]:
            raise forms.ValidationError({"points": "Not enough bonus points to redeem"})
        if cleaned_data["points"] <= 0:
            raise forms.ValidationError(
                {"points": "Points must be greater than zero to redeem."}
            )


class DisciplinaryActionForm(ModelForm):
    class Meta:
        model = DisciplinaryAction
        fields = "__all__"
        exclude = ["objects", "is_active"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }

    action = forms.ModelChoiceField(
        queryset=Actiontype.objects.all(),
        label=_("Action"),
        widget=forms.Select(
            attrs={
                "class": "oh-select oh-select-2 select2-hidden-accessible",
                "onchange": "actionTypeChange($(this))",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        action_choices = [("", _("---Choose Action---"))] + list(
            self.fields["action"].queryset.values_list("id", "title")
        )
        self.fields["action"].choices = action_choices
        if self.instance.pk is None:
            self.fields["action"].choices += [("create", _("Create new action type "))]

    def as_p(self):
        """
        Render the form fields as HTML table rows with Bootstrap styling.
        """
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html


class ActiontypeForm(ModelForm):
    class Meta:
        model = Actiontype
        fields = "__all__"
        exclude = ["is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["action_type"].widget.attrs.update(
            {
                "onchange": "actionChange($(this))",
            }
        )


class EmployeeTagForm(ModelForm):
    """
    Employee Tags form
    """

    class Meta:
        """
        Meta class for additional options
        """

        model = EmployeeTag
        fields = "__all__"
        exclude = ["is_active"]
        widgets = {"color": TextInput(attrs={"type": "color", "style": "height:50px"})}


class EventalenderForm(ModelForm):

    verbose_name = "Event Calender"

    class Meta:
        model = EventCalender
        fields = "__all__"
        exclude = ["status", "is_active"]
        widgets = {
            "employee_id": forms.HiddenInput(),
            "event_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "oh-input  w-100"}
            ),
            "reminder_date": forms.DateTimeInput(
                attrs={"type": "datetime-local", "class": "oh-input  w-100"}
            ),
        }

    def as_p(self):
        context = {"form": self}
        table_html = render_to_string("common_form.html", context)
        return table_html

class EmployeeGeneralSettingPrefixForm(forms.ModelForm):

    class Meta:

        model = EmployeeGeneralSetting
        exclude = ["objects"]
        widgets = {
            "badge_id_prefix": forms.TextInput(attrs={"class": "oh-input w-100"}),
            "company_id": forms.Select(attrs={"class": "oh-select oh-select-2 w-100"}),
        }


class IncidentForm(ModelForm):
    """form to create a new Document"""

    verbose_name = "Incident"

    class Meta:
        model = EmployeeIncident
        fields = "__all__"
        exclude = [ "status",  "is_active"]
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
