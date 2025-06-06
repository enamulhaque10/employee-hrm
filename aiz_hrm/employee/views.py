"""
views.py

This module contains the view functions for handling HTTP requests and rendering
responses in your application.

Each view function corresponds to a specific URL route and performs the necessary
actions to handle the request, process data, and generate a response.

This module is part of the recruitment project and is intended to
provide the main entry points for interacting with the application's functionality.
"""

import ast
import calendar
import json
import operator
import os
import re
import threading
from datetime import date, datetime, timedelta
from urllib.parse import parse_qs

import pandas as pd
from django.apps import apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import F, ProtectedError, Count
from django.db.models.query import QuerySet
from django.forms import DateInput, Select
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as __
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.core.serializers.json import DjangoJSONEncoder
from io import BytesIO
import requests
from PIL import Image as PILImage
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dateutil import parser
from dateutil.relativedelta import relativedelta
import time
from django.db import transaction
from time import sleep




from accessibility.decorators import enter_if_accessible
from accessibility.methods import update_employee_accessibility_cache
from accessibility.middlewares import ACCESSIBILITY_CACHE_USER_KEYS
from accessibility.models import DefaultAccessibility
from base.forms import ModelForm
from base.methods import (
    choosesubordinates,
    filtersubordinates,
    filtersubordinatesemployeemodel,
    get_key_instances,
    get_pagination,
    sortby,
)
from base.models import (
    Company,
    Department,
    EmailLog,
    EmployeeShift,
    EmployeeType,
    JobPosition,
    JobRole,
    RotatingShiftAssign,
    RotatingWorkTypeAssign,
    ShiftRequest,
    WorkType,
    WorkTypeRequest,
    clear_messages,
    EmployeeSection,
    EmployeeUnit,
)
from employee.filters import DocumentRequestFilter, EmployeeFilter, EmployeeReGroup
from employee.forms import (
    BonusPointAddForm,
    BonusPointRedeemForm,
    BulkUpdateFieldForm,
    EmployeeBankDetailsForm,
    EmployeeBankDetailsUpdateForm,
    EmployeeExportExcelForm,
    EmployeeForm,
    EmployeeGeneralSettingPrefixForm,
    EmployeeNoteForm,
    EmployeeTagForm,
    EmployeeWorkInformationForm,
    EmployeeWorkInformationUpdateForm,
    excel_columns,
    IncidentForm,
    EventalenderForm,
)
from employee.methods.methods import (
    bulk_create_department_import,
    bulk_create_employee_import,
    bulk_create_employee_types,
    bulk_create_job_position_import,
    bulk_create_job_role_import,
    bulk_create_shifts,
    bulk_create_user_import,
    bulk_create_work_info_import,
    bulk_create_work_types,
    convert_nan,
    get_ordered_badge_ids,
    set_initial_password,
    #bulk_create_job_section_import,
    #bulk_create_job_unit_import,
    bulk_create_job_experience_info_import,
    bulk_create_educational_info_import,
    bulk_create_professional_training_import,
    bulk_create_job_reference_import
)
from employee.models import (
    BonusPoint,
    Employee,
    EmployeeBankDetails,
    EmployeeGeneralSetting,
    EmployeeNote,
    EmployeeTag,
    EmployeeWorkInformation,
    NoteFiles,
    EmployeeIncident,
    EventCalender,
)
from aiz.decorators import (
    hx_request_required,
    logger,
    login_required,
    manager_can_enter,
    owner_can_enter,
    permission_required,
)
from aiz.filters import aizPaginator
from aiz.group_by import group_by_queryset
from aiz.aiz_settings import aiz_DATE_FORMATS
from aiz.methods import get_aiz_model_class
from aiz_audit.models import AccountBlockUnblock, HistoryTrackingFields
from aiz_documents.forms import (
    DocumentForm,
    DocumentRejectForm,
    DocumentRequestForm,
    DocumentUpdateForm,
    DocumentCategoryForm,
    IncidentForm,
)
from aiz_documents.models import Document, DocumentRequest, DocumentCategory
from aiz_job_experiences.forms import (
    JobExperienceUpdateForm,
    JobExperienceForm
)
from aiz_employee_education.forms import (
    EmployeeEducationUpdateForm,
    EmployeeEducationForm
)
from aiz_employee_training.forms import (
    EmployeeTrainingUpdateForm,
    EmployeeTrainingForm
)
from aiz_job_reference.forms import (
    JobReferenceUpdateForm,
    JobReferenceForm
)
from aiz_job_experiences.models import EmployeeJobExperiences
from aiz_employee_education.models import EmployeeEducation
from aiz_employee_training.models import EmployeeTraining
from aiz_job_reference.models import JobReference
from notifications.signals import notify
from employee.tasks import send_event_reminders




# schedule.every().day.at("09:00").do(send_event_reminders)

# while True:
#     schedule.run_pending()
#     time.sleep(60)





def return_none(a, b):
    return None


operator_mapping = {
    "equal": operator.eq,
    "notequal": operator.ne,
    "lt": operator.lt,
    "gt": operator.gt,
    "le": operator.le,
    "ge": operator.ge,
    "icontains": operator.contains,
    "range": return_none,
}
filter_mapping = {
    "work_type_id": {
        "filter": lambda employee, allowance: {
            "employee_id": employee,
            "work_type_id__id": allowance.work_type_id.id,
            "attendance_validated": True,
        }
    },
    "shift_id": {
        "filter": lambda employee, allowance,: {
            "employee_id": employee,
            "shift_id__id": allowance.shift_id.id,
            "attendance_validated": True,
        }
    },
    "overtime": {
        "filter": lambda employee, allowance: {
            "employee_id": employee,
            "attendance_overtime_approve": True,
            "attendance_validated": True,
        }
    },
    "attendance": {
        "filter": lambda employee, allowance: {
            "employee_id": employee,
            "attendance_validated": True,
        }
    },
}


def _check_reporting_manager(request, *args, **kwargs):
    if kwargs.get("obj_id"):
        obj_id = kwargs["obj_id"]
        emp = Employee.objects.get(id=obj_id)
        re_manager = None
        if emp.employee_work_info.reporting_manager_id != None:
            re_manager = emp.employee_work_info.reporting_manager_id
        employee = request.user.employee_get
        if re_manager != None:
            return re_manager == employee
        else:
            return False
    return request.user.employee_get.reporting_manager.exists()


# Create your views here.
@login_required
def get_language_code(request):
    """
    Retrieve the language code for the current request.

    This view function extracts the LANGUAGE_CODE from the request object and
    returns it as a JSON response. This function requires the user to be logged in.
    """
    language_code = request.LANGUAGE_CODE
    return JsonResponse({"language_code": language_code})


@login_required
def employee_profile(request):
    """
    This method is used to view own profile of employee.
    """
    employee = request.user.employee_get
    today = datetime.today()
    now = timezone.now()
    return render(
        request,
        "employee/profile/profile_view.html",
        {
            "employee": employee,
            "current_date": today,
            "now": now,
        },
    )


@login_required
@enter_if_accessible(
    feature="profile_edit",
    perm="employee.change_employee",
)
def self_info_update(request):
    """
    This method is used to update own profile of an employee.
    """
    user = request.user
    employee = Employee.objects.filter(employee_user_id=user).first()
    badge_id = employee.badge_id
    bank_form = EmployeeBankDetailsForm(
        instance=EmployeeBankDetails.objects.filter(employee_id=employee).first()
    )
    form = EmployeeForm(instance=Employee.objects.filter(employee_user_id=user).first())
    if request.POST:
        if request.POST.get("employee_first_name") is not None:
            instance = Employee.objects.filter(employee_user_id=request.user).first()
            form = EmployeeForm(request.POST, instance=instance)
            if form.is_valid():
                instance = form.save(commit=False)
                instance.employee_user_id = user
                if instance.badge_id is None:
                    instance.badge_id = badge_id
                instance.save()
                messages.success(request, _("Profile updated."))
        elif request.POST.get("any_other_code1") is not None:
            instance = EmployeeBankDetails.objects.filter(employee_id=employee).first()
            bank_form = EmployeeBankDetailsForm(request.POST, instance=instance)
            if bank_form.is_valid():
                instance = bank_form.save(commit=False)
                instance.employee_id = employee
                instance.save()
                messages.success(request, _("Bank details updated."))
    return render(
        request,
        "employee/profile/profile.html",
        {
            "form": form,
            "bank_form": bank_form,
        },
    )


def profile_edit_access(request, emp_id):
    feature = request.GET.get("feature", None)
    accessibility = DefaultAccessibility.objects.filter(feature=feature).first()
    if accessibility:
        employees = Employee.objects.filter(id=emp_id)

        if employee := employees.first():
            if employee in accessibility.employees.all():
                accessibility.employees.remove(employee)
            else:
                accessibility.employees.add(employee)

            user_cache_key = ACCESSIBILITY_CACHE_USER_KEYS.get(
                employees.first().employee_user_id.id, None
            )
            if user_cache_key:
                cache.delete(user_cache_key[-1])
                update_employee_accessibility_cache(user_cache_key[-1], employee)

    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@enter_if_accessible(
    feature="employee_detailed_view",
    perm="employee.view_employee",
    method=_check_reporting_manager,
)
def employee_view_individual(request, obj_id, **kwargs):
    """
    This method is used to view profile of an employee.
    """
    employee = Employee.objects.get(id=obj_id)
    employee_leaves = (
        employee.available_leave.all() if apps.is_installed("leave") else None
    )
    enabled_block_unblock = (
        AccountBlockUnblock.objects.exists()
        and AccountBlockUnblock.objects.first().is_enabled
    )
    # Retrieve the filtered employees from the session
    filtered_employee_ids = request.session.get("filtered_employees", [])
    filtered_employees = Employee.objects.filter(id__in=filtered_employee_ids)

    request_ids_str = json.dumps(
        [
            instance.id
            for instance in paginator_qry(
                filtered_employees, request.GET.get("page")
            ).object_list
        ]
    )

    # Convert the string to an actual list of integers
    requests_ids = (
        ast.literal_eval(request_ids_str)
        if isinstance(request_ids_str, str)
        else request_ids_str
    )

    employee_id = employee.id
    previous_id = None
    next_id = None

    for index, req_id in enumerate(requests_ids):
        if req_id == employee_id:

            if index == len(requests_ids) - 1:
                next_id = None
            else:
                next_id = requests_ids[index + 1]
            if index == 0:
                previous_id = None
            else:
                previous_id = requests_ids[index - 1]
            break

    context = {
        "employee": employee,
        "previous": previous_id,
        "next": next_id,
        "requests_ids": requests_ids,
        "current_date": date.today(),
        "leave_request_ids": json.dumps([]),
        "enabled_block_unblock": enabled_block_unblock,
    }
    # if the requesting user opens own data
    if request.user.employee_get == employee:
        context["user_leaves"] = employee_leaves
    else:
        context["employee_leaves"] = employee_leaves

    return render(
        request,
        "employee/view/individual.html",
        context,
    )


@login_required
@hx_request_required
def about_tab(request, obj_id, **kwargs):
    """
    This method is used to view profile of an employee.
    """
    employee = Employee.objects.get(id=obj_id)
    contracts = employee.contract_set.all() if apps.is_installed("payroll") else None
    employee_leaves = (
        employee.available_leave.all() if apps.is_installed("leave") else None
    )
    
    return render(
        request,
        "tabs/personal_tab.html",
        {
            "employee": employee,
            "employee_leaves": employee_leaves,
            "contracts": contracts,
        },
    )


@login_required
@hx_request_required
@owner_can_enter("perms.employee.view_employee", Employee)
def shift_tab(request, emp_id):
    """
    This function is used to view shift tab of an employee in employee individual & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    emp_id (int): The id of the employee.

    Returns: return shift-tab template
    """
    employee = Employee.objects.get(id=emp_id)
    work_type_requests = WorkTypeRequest.objects.filter(employee_id=emp_id)
    work_type_requests_ids = json.dumps(
        [instance.id for instance in work_type_requests]
    )
    rshift_assign = RotatingShiftAssign.objects.filter(employee_id=emp_id)
    rshift_assign_ids = json.dumps([instance.id for instance in rshift_assign])
    rwork_type_assign = RotatingWorkTypeAssign.objects.filter(employee_id=emp_id)
    rwork_type_assign_ids = json.dumps([instance.id for instance in rwork_type_assign])
    shift_requests = ShiftRequest.objects.filter(employee_id=emp_id)
    shift_requests_ids = json.dumps([instance.id for instance in shift_requests])

    context = {
        "work_data": work_type_requests,
        "work_type_requests_ids": work_type_requests_ids,
        "rshift_assign": rshift_assign,
        "rshift_assign_ids": rshift_assign_ids,
        "rwork_type_assign": rwork_type_assign,
        "rwork_type_assign_ids": rwork_type_assign_ids,
        "shift_data": shift_requests,
        "shift_requests_ids": shift_requests_ids,
        "emp_id": emp_id,
        "employee": employee,
    }
    return render(request, "tabs/shift-tab.html", context=context)


@login_required
@manager_can_enter("aiz_documents.view_documentrequest")
def document_request_view(request):
    """
    This function is used to view documents requests of employees.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns: return document_request template
    """
    previous_data = request.GET.urlencode()
    filter_class = DocumentRequestFilter()
    document_requests = DocumentRequest.objects.all()
    documents = Document.objects.filter(document_request_id__isnull=False)
    documents = filtersubordinates(
        request=request,
        perm="aiz_documents.view_documentrequest",
        queryset=documents,
    )
    documents = group_by_queryset(
        documents, "document_request_id", request.GET.get("page"), "page"
    )
    data_dict = parse_qs(previous_data)
    get_key_instances(Document, data_dict)
    context = {
        "document_requests": document_requests,
        "documents": documents,
        "f": filter_class,
        "pd": previous_data,
        "filter_dict": data_dict,
    }
    return render(request, "documents/document_requests.html", context=context)


@login_required
@hx_request_required
@manager_can_enter("aiz_documents.view_documentrequest")
def document_filter_view(request):
    """
    This method is used to filter employee.
    """
    document_requests = DocumentRequest.objects.all()
    previous_data = request.GET.urlencode()
    documents = DocumentRequestFilter(request.GET).qs
    documents = documents.exclude(document_request_id__isnull=True).order_by(
        "-document_request_id"
    )
    documents = group_by_queryset(
        documents, "document_request_id", request.GET.get("page"), "page"
    )
    # documents = paginator_qry(documents,request.GET.get("page"))
    data_dict = parse_qs(previous_data)
    get_key_instances(Document, data_dict)

    return render(
        request,
        "documents/requests.html",
        {
            "documents": documents,
            "f": EmployeeFilter(request.GET),
            "pd": previous_data,
            "filter_dict": data_dict,
            "document_requests": document_requests,
        },
    )


@login_required
@hx_request_required
@manager_can_enter("aiz_documents.add_documentrequest")
def document_request_create(request):
    """
    This function is used to create document requests of an employee in employee requests view.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns: return document_request_create_form template
    """
    form = DocumentRequestForm()
    form = choosesubordinates(request, form, "aiz_documents.add_documentrequest")
    if request.method == "POST":
        form = DocumentRequestForm(request.POST)
        form = choosesubordinates(
            request, form, "aiz_documents.add_documentrequest"
        )
        if form.is_valid():
            form = form.save()
            messages.success(request, _("Document request created successfully"))
            employees = [user.employee_user_id for user in form.employee_id.all()]

            notify.send(
                request.user.employee_get,
                recipient=employees,
                verb=f"{request.user.employee_get} requested a document.",
                verb_ar=f"طلب {request.user.employee_get} مستنداً.",
                verb_de=f"{request.user.employee_get} hat ein Dokument angefordert.",
                verb_es=f"{request.user.employee_get} solicitó un documento.",
                verb_fr=f"{request.user.employee_get} a demandé un document.",
                redirect=reverse("employee-profile"),
                icon="chatbox-ellipses",
            )
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
    }
    return render(
        request, "documents/document_request_create_form.html", context=context
    )


@login_required
@hx_request_required
@manager_can_enter("aiz_documents.change_documentrequest")
def document_request_update(request, id):
    """
    This function is used to update document requests of an employee in employee requests view.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns: return document_request_create_form template
    """
    document_request = get_object_or_404(DocumentRequest, id=id)
    documents = Document.objects.filter(document_request_id=document_request.id)
    form = DocumentRequestForm(instance=document_request)
    if request.method == "POST":
        form = DocumentRequestForm(request.POST, instance=document_request)
        if form.is_valid():
            doc_obj = form.save()
            doc_obj.employee_id.set(
                Employee.objects.filter(id__in=form.data.getlist("employee_id"))
            )
            documents.exclude(employee_id__in=doc_obj.employee_id.all()).delete()
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "document_request": document_request,
    }
    return render(
        request, "documents/document_request_create_form.html", context=context
    )


@login_required
@hx_request_required
@owner_can_enter("aiz_documents.view_document", Employee)
def document_tab(request, emp_id):
    """
    This function is used to view documents tab of an employee in employee individual
    & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    emp_id (int): The id of the employee.

    Returns: return document_tab template
    """

    form = DocumentUpdateForm(request.POST, request.FILES)
    documents = Document.objects.filter(employee_id=emp_id)

    context = {
        "documents": documents,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/document_tab.html", context=context)



@login_required
@hx_request_required
@owner_can_enter("aiz_documents.view_document", Employee)
def employee_document_tab(request, emp_id):
    """
    This function is used to view documents tab of an employee in employee individual
    & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    emp_id (int): The id of the employee.

    Returns: return document_tab template
    """

    if request.method == "POST":
        form = DocumentUpdateForm(request.POST, request.FILES)
    else:
        form = DocumentUpdateForm()

    
    documents = Document.objects.filter(employee_id=emp_id)

    context = {
        "documents": documents,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "employee/update_form/document_tab.html", context=context)

def employee_document_public_tab(request, emp_id):
    
    form = DocumentUpdateForm(request.POST, request.FILES)
    documents = Document.objects.filter(employee_id=emp_id)

    context = {
        "documents": documents,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/document_public_tab.html", context=context)


def document_category_search(request, emp_id):
    
    form = DocumentUpdateForm(request.POST, request.FILES)
    documents = Document.objects.filter(employee_id=emp_id)
    category_id = request.GET.get("category")
    if category_id:
        documents = documents.filter(document_category_id=category_id)

    context = {
        "documents": documents,
        "form": form,
        "emp_id": emp_id,
    }
    
    return  render(request, "tabs/document_category_wise_list.html", context=context)

def incident_document_public_tab(request, emp_id):
   
    form = IncidentForm(request.POST, request.FILES)
    
    documents = EmployeeIncident.objects.filter(employee_id=emp_id)

    context = {
        "documents": documents,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/incident_document_tab.html", context=context)



def employee_incident_document_tab(request, emp_id):
    """
    This function is used to view documents tab of an employee in employee individual
    & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    emp_id (int): The id of the employee.

    Returns: return document_tab template
    """
    form = IncidentForm(request.POST, request.FILES)
    

    
    documents = EmployeeIncident.objects.filter(employee_id=emp_id)

    context = {
        "documents": documents,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/incident_document.html", context=context)


@login_required
@hx_request_required
@owner_can_enter("aiz_job_experiences.view_job_experience", Employee)
def job_experiences_tab(request, emp_id):
    form = JobExperienceUpdateForm(request.POST, request.FILES)
    job_experiences = EmployeeJobExperiences.objects.filter(employee_id=emp_id)

    context = {
        "job_experiences": job_experiences,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/job_experience_tab.html", context=context)

@login_required
@hx_request_required
@owner_can_enter("aiz_job_experiences.view_employee_education", Employee)
def employee_education_tab(request, emp_id):
    form = EmployeeEducationUpdateForm(request.POST, request.FILES)
    employee_education = EmployeeEducation.objects.filter(employee_id=emp_id)

    context = {
        "employee_educations": employee_education,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/employee_education_tab.html", context=context)

@login_required
@hx_request_required
@owner_can_enter("aiz_job_experiences.view_employee_training", Employee)
def employee_training_tab(request, emp_id):
    form = EmployeeTrainingUpdateForm(request.POST, request.FILES)
    employee_training = EmployeeTraining.objects.filter(employee_id=emp_id)

    context = {
        "employee_trainings": employee_training,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/employee_training_tab.html", context=context)


def event_calender_tab(request, emp_id):
    form = EventalenderForm(request.POST, request.FILES)
    event_calenders = EventCalender.objects.all()

    calender_events = []

    for event in event_calenders:
       item =  {
           "id": event.id,
            "title": event.event_title,
            "start": event.event_date.strftime('%Y-%m-%d'),
            "reminder": event.reminder_date.strftime('%Y-%m-%d'),
            "description": event.event_description,
        }
       calender_events.append(item)
       

    context = {
        "event_calenders": event_calenders,
        "form": form,
        "emp_id": emp_id,
        "calendar_events_json": json.dumps(calender_events, cls=DjangoJSONEncoder),
    }
    return render(request, "tabs/event_calender.html", context=context)


@login_required
@hx_request_required
@owner_can_enter("aiz_job_reference.view_job_reference", Employee)
def job_reference_tab(request, emp_id):
    form = JobReferenceUpdateForm(request.POST, request.FILES)
    job_reference = JobReference.objects.filter(employee_id=emp_id)

    context = {
        "job_references": job_reference,
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/job_reference_tab.html", context=context)


@login_required
@hx_request_required
@owner_can_enter("aiz_documents.add_document", Employee)
def document_create(request, emp_id):
    """
    This function is used to create documents from employee individual & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    emp_id (int): The id of the employee

    Returns: return document_tab template
    """
    print(emp_id, 'emp')
    employee_id = Employee.objects.get(id=emp_id)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _("Document created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")
    else:
        form = DocumentForm(initial={"employee_id": employee_id, "expiry_date": None})

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/document_create_form.html", context=context)

@login_required
@hx_request_required
@owner_can_enter("aiz_documents.add_document", Employee)
def incident_document_create(request, emp_id):
  
    employee_id = Employee.objects.get(id=emp_id)
    form = IncidentForm(initial={"employee_id": employee_id})
    if request.method == "POST":
        form = IncidentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _(" Incident Document created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/incident_doccument_create_form.html", context=context)

def document_create_public(request, emp_id):
    
    employee_id = Employee.objects.get(id=emp_id)
    if request.method == "POST":
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee_id = employee_id
            document.save()
            messages.success(request, _("Document created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")
    else:
            form = DocumentForm(initial={"employee_id": employee_id, "expiry_date": None})

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/document_create_form.html", context=context)



def incident_document_create_public(request, emp_id):
    
    employee_id = Employee.objects.get(id=emp_id)
    form = IncidentForm(initial={"employee_id": employee_id})
    if request.method == "POST":
        form = IncidentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _(" Incident Document created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/incident_create_form.html", context=context)


@login_required
@hx_request_required
def document_category_create(request):
    """
    This method renders form and template to create document category
    """
    print(request, 'request')
    dynamic = request.GET.get("dynamic") if request.GET.get("dynamic") else ""
    form = DocumentCategoryForm()
    if request.method == "POST":
        form = DocumentCategoryForm(request.POST)
        if form.is_valid():
            print("vitore aschi")
            form.save()
            form = DocumentCategoryForm()
            messages.success(request, _("Category has been created successfully!"))
            return HttpResponse("<script>window.location.reload()</script>")
    print(form, 'form')
    return render(
        request,
        "tabs/document_category_form.html",
        {
            "form": form,
            "dynamic": dynamic
        },
    )

@login_required
@hx_request_required
@owner_can_enter("aiz_documents.add_document", Employee)
def document_category_update(request, id, **kwargs):
    """
    This method is used to update document category Section
    args:
        id : document category instance id

    """
    category_section = DocumentCategory.find(id)
    form = DocumentCategoryForm(instance=category_section)
    if request.method == "POST":
        form = DocumentCategoryForm(request.POST, instance=category_section)
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, _("Category Section updated."))
            return HttpResponse("<script>window.location.reload()</script>")
    return render(
        request,
        "tabs/document_category_form",
        {"form": form, "category_section": category_section},
    )


@login_required
@hx_request_required
@owner_can_enter("aiz_job_experiences.add_document", Employee)
def job_experience_create(request, emp_id):
    employee_id = Employee.objects.get(id=emp_id)
    form = JobExperienceForm(initial={"employee_id": employee_id})
    if request.method == "POST":
        form = JobExperienceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Job Experience created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/job_experiences_create_form.html", context=context)


@login_required
@hx_request_required
@owner_can_enter("aiz_job_refernce.add_document", Employee)
def job_reference_create(request, emp_id):
    employee_id = Employee.objects.get(id=emp_id)
    form = JobReferenceForm(initial={"employee_id": employee_id})
    if request.method == "POST":
        form = JobReferenceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Job Reference created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/job_reference_create_form.html", context=context)

@login_required
@hx_request_required
@owner_can_enter("aiz_employee_education.add_document", Employee)
def employee_education_create(request, emp_id):
    employee_id = Employee.objects.get(id=emp_id)
    form = EmployeeEducationForm(initial={"employee_id": employee_id})
    if request.method == "POST":
        form = EmployeeEducationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Employee Education created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/employee_education_create_form.html", context=context)

@login_required
@hx_request_required
@owner_can_enter("aiz_employee_training.add_document", Employee)
def employee_training_create(request, emp_id):
    employee_id = Employee.objects.get(id=emp_id)
    form = EmployeeTrainingForm(initial={"employee_id": employee_id})
    if request.method == "POST":
        form = EmployeeTrainingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Employee Training created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/employee_training_create_form.html", context=context)

@login_required
@hx_request_required
def event_calender_create(request, emp_id):
    employee_id = Employee.objects.get(id=emp_id)
    form = EventalenderForm(initial={"employee_id": employee_id})
    if request.method == "POST":
        form = EventalenderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Event Calender created successfully."))
            return HttpResponse("<script>window.location.reload();</script>")

    context = {
        "form": form,
        "emp_id": emp_id,
    }
    return render(request, "tabs/htmx/event_calender_create.html", context=context)


@login_required
def update_document_title(request, id):
    """
    This function is used to create documents from employee individual & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.

    Returns: return document_tab template
    """
    document = get_object_or_404(Document, id=id)
    name = request.POST.get("title")
    if request.method == "POST":
        document.title = name
        document.save()
        messages.success(request, _("Document title updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_incident_document_title(request, id):
    
    document = get_object_or_404(EmployeeIncident, id=id)
    name = request.POST.get("title")
    if request.method == "POST":
        document.title = name
        document.save()
        messages.success(request, _("Incident title updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")


@login_required
def update_job_experience_title(request, id):
    document = get_object_or_404(EmployeeJobExperiences, id=id)
    name = request.POST.get("title")
    if request.method == "POST":
        document.title = name
        document.save()
        messages.success(request, _("Title updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_job_experience_company_name(request, id):
    document = get_object_or_404(EmployeeJobExperiences, id=id)
    company_name = request.POST.get("company_name")
    if request.method == "POST":
        document.company_name = company_name
        document.save()
        messages.success(request, _("Company Name updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_job_experience_designation(request, id):
    document = get_object_or_404(EmployeeJobExperiences, id=id)
    designation = request.POST.get("designation")
    if request.method == "POST":
        document.designation = designation
        document.save()
        messages.success(request, _("Designation updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_job_experience_year_of_experience(request, id):
    document = get_object_or_404(EmployeeJobExperiences, id=id)
    year_of_experience = request.POST.get("year_of_experience")
    if request.method == "POST":
        document.year_of_experience = year_of_experience
        document.save()
        messages.success(request, _("Year Of Experience updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_employee_education_education_label(request, id):
    document = get_object_or_404(EmployeeEducation, id=id)
    education_label = request.POST.get("education_label")
    if request.method == "POST":
        document.education_label = education_label
        document.save()
        messages.success(request, _("Education Label updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_employee_education_institution_name(request, id):
    document = get_object_or_404(EmployeeEducation, id=id)
    institution_name = request.POST.get("institution_name")
    if request.method == "POST":
        document.institution_name = institution_name
        document.save()
        messages.success(request, _("Institution Name updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_employee_education_subject(request, id):
    document = get_object_or_404(EmployeeEducation, id=id)
    subject = request.POST.get("subject")
    if request.method == "POST":
        document.subject = subject
        document.save()
        messages.success(request, _("Subject updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_employee_education_passing_year(request, id):
    document = get_object_or_404(EmployeeEducation, id=id)
    passing_year = request.POST.get("passing_year")
    if request.method == "POST":
        document.passing_year = passing_year
        document.save()
        messages.success(request, _("Passing Year updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_employee_training_training_name(request, id):
    document = get_object_or_404(EmployeeTraining, id=id)
    training_name = request.POST.get("training_name")
    if request.method == "POST":
        document.training_name = training_name
        document.save()
        messages.success(request, _("Training Name updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_event_calender_title(request, id):
    event = get_object_or_404(EventCalender, id=id)
    event_name = request.POST.get("event_title")
    if request.method == "POST":
        event.event_title = event_name
        event.save()
        messages.success(request, _("Event Title updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_event_calender_event_date(request, id):
    event = get_object_or_404(EventCalender, id=id)
    event_date= request.POST.get("event_date")
    date_obj = parser.parse(event_date)
    #formatted_date = date_obj.strftime("%Y-%m-%d")

    if request.method == "POST":
        event.event_date = date_obj
        event.save()
        messages.success(request, _("Event Date updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_event_calender_event_description(request, id):
    event = get_object_or_404(EventCalender, id=id)
    event_des = request.POST.get("event_description")
    if request.method == "POST":
        event.event_description = event_des
        event.save()
        messages.success(request, _("Event Description updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")


@login_required
def update_event_calender_event_reminder_mail(request, id):
    event = get_object_or_404(EventCalender, id=id)
    event_reminder_mail = request.POST.get("reminder_person")
    if request.method == "POST":
        event.reminder_person = event_reminder_mail
        event.save()
        messages.success(request, _("Event Reminder Person updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")


@login_required
def update_event_calender_reminder_date(request, id):
    event = get_object_or_404(EventCalender, id=id)
    reminder_date = request.POST.get("reminder_date")
    date_obj = parser.parse(reminder_date)
    #date_obj = datetime.strptime(reminder_date, "%B %d, %Y, %I:%M %p")
    # formatted_date = date_obj.strftime("%Y-%m-%d")
    if request.method == "POST":
        event.reminder_date = date_obj
        event.save()
        messages.success(request, _("Event Reminder updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")


@login_required
def update_employee_training_institution_name(request, id):
    document = get_object_or_404(EmployeeTraining, id=id)
    institution_name = request.POST.get("institution_name")
    if request.method == "POST":
        document.institution_name = institution_name
        document.save()
        messages.success(request, _("Institution Name updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")


@login_required
def update_job_reference_reference_name(request, id):
    document = get_object_or_404(JobReference, id=id)
    reference_name = request.POST.get("reference_name")
    if request.method == "POST":
        document.reference_name = reference_name
        document.save()
        messages.success(request, _("Reference Name updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_job_reference_department(request, id):
    document = get_object_or_404(JobReference, id=id)
    department = request.POST.get("department")
    if request.method == "POST":
        document.department = department
        document.save()
        messages.success(request, _("Department updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_job_reference_company_name(request, id):
    document = get_object_or_404(JobReference, id=id)
    company_name = request.POST.get("company_name")
    if request.method == "POST":
        document.company_name = company_name
        document.save()
        messages.success(request, _("Company Name updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_job_reference_mobile_number(request, id):
    document = get_object_or_404(JobReference, id=id)
    mobile_number = request.POST.get("mobile_number")
    if request.method == "POST":
        document.mobile_number = mobile_number
        document.save()
        messages.success(request, _("Mobile Number updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
def update_job_reference_reference_name(request, id):
    document = get_object_or_404(JobReference, id=id)
    reference_name = request.POST.get("reference_name")
    if request.method == "POST":
        document.reference_name = reference_name
        document.save()
        messages.success(request, _("Reference Name updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
@hx_request_required
def document_delete(request, id):
    """
    Handle the deletion of a document, with permissions and error handling.

    This view function attempts to delete a document specified by its ID.
    If the user does not have the "delete_document" permission, it restricts
    deletion to documents owned by the user. It provides appropriate success
    or error messages based on the outcome. If the document is protected and
    cannot be deleted, it handles the exception and informs the user.
    """
    try:
        document = Document.objects.filter(id=id)
        if not request.user.has_perm("aiz_documents.delete_document"):
            document = document.filter(
                employee_id__employee_user_id=request.user
            ).exclude(document_request_id__isnull=False)
        if document:
            document_first = document.first()
            document.delete()
            messages.success(
                request,
                _(
                    f"Document request {document_first} for {document_first.employee_id} deleted successfully"
                ),
            )
            referrer = request.META.get("HTTP_REFERER", "")
            referrer = "/" + "/".join(referrer.split("/")[3:])
            if referrer.startswith("/employee/employee-view/") or referrer.endswith(
                "/employee/employee-profile/"
            ):
                existing_documents = Document.objects.filter(
                    employee_id=document_first.employee_id
                )
                if not existing_documents:
                    return HttpResponse(
                        f"""
                            <span hx-get='/employee/document-tab/{document_first.employee_id.id}?employee_view=true'
                            hx-target='#document_target' hx-trigger='load'></span>
                        """
                    )
            return HttpResponse()
        else:
            messages.error(request, _("Document not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this document."))
    return HttpResponse("<script>window.location.reload();</script>")


@login_required
@hx_request_required
def incident_document_delete(request, id):
  
    try:
        document = EmployeeIncident.objects.filter(id=id)
        if not request.user.has_perm("aiz_documents.delete_document"):
            document = document.filter(
                employee_id__employee_user_id=request.user
            ).exclude(document_request_id__isnull=False)
        if document:
            document_first = document.first()
            document.delete()
            messages.success(
                request,
                _(
                    f"Incident request {document_first} for {document_first.employee_id} deleted successfully"
                ),
            )
            referrer = request.META.get("HTTP_REFERER", "")
            referrer = "/" + "/".join(referrer.split("/")[3:])
            if referrer.startswith("/employee/employee-view/") or referrer.endswith(
                "/employee/employee-profile/"
            ):
                existing_documents = EmployeeIncident.objects.filter(
                    employee_id=document_first.employee_id
                )
                if not existing_documents:
                    return HttpResponse(
                        f"""
                            <span hx-get='/employee/document-tab/{document_first.employee_id.id}?employee_view=true'
                            hx-target='#document_target' hx-trigger='load'></span>
                        """
                    )
            return HttpResponse()
        else:
            messages.error(request, _("Incident not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this document."))
    return HttpResponse("<script>window.location.reload();</script>")


@login_required
@hx_request_required
def job_experience_delete(request, id):
    try:
        job_experience = EmployeeJobExperiences.objects.filter(id=id)
        if job_experience:
            job_experience.delete()
            messages.success(
                request,
                _(
                    f"Job Experience deleted successfully"
                ),
            )
        else:
            messages.error(request, _("Job Experience not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this Job Experience."))
    return HttpResponse("<script>window.location.reload();</script>")

@login_required
@hx_request_required
def employee_education_delete(request, id):
    try:
        employee_education = EmployeeEducation.objects.filter(id=id)
        if employee_education:
            employee_education.delete()
            messages.success(
                request,
                _(
                    f"Employee Education deleted successfully"
                ),
            )
        else:
            messages.error(request, _("Employee Education not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this Employee Education."))
    return HttpResponse("<script>window.location.reload();</script>")

@login_required
@hx_request_required
def employee_training_delete(request, id):
    try:
        employee_training = EmployeeTraining.objects.filter(id=id)
        if employee_training:
            employee_training.delete()
            messages.success(
                request,
                _(
                    f"Employee Training deleted successfully"
                ),
            )
        else:
            messages.error(request, _("Employee Training not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this Employee Training."))
    return HttpResponse("<script>window.location.reload();</script>")



@login_required
@hx_request_required
def event_calender_delete(request, id):
    try:
        calender = EventCalender.objects.filter(id=id)
        if calender:
            calender.delete()
            messages.success(
                request,
                _(
                    f"Event calender deleted successfully"
                ),
            )
        else:
            messages.error(request, _("Event calender not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this Event Calender."))
    return HttpResponse("<script>window.location.reload();</script>")


@login_required
@hx_request_required
def job_reference_delete(request, id):
    try:
        job_reference = JobReference.objects.filter(id=id)
        if job_reference:
            job_reference.delete()
            messages.success(
                request,
                _(
                    f"Job Reference deleted successfully"
                ),
            )
        else:
            messages.error(request, _("Job Reference not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this Job Reference."))
    return HttpResponse("<script>window.location.reload();</script>")

@login_required
@hx_request_required
def file_upload(request, id):
    """
    This function is used to upload documents of an employee in employee individual & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    id (int): The id of the document.

    Returns: return document_form template
    """

    document_item = Document.objects.get(id=id)
    form = DocumentUpdateForm(instance=document_item)
    if request.method == "POST":
        form = DocumentUpdateForm(request.POST, request.FILES, instance=document_item)
        if form.is_valid():
            form.save()
            messages.success(request, _("Document uploaded successfully"))
            try:
                notify.send(
                    request.user.employee_get,
                    recipient=request.user.employee_get.get_reporting_manager().employee_user_id,
                    verb=f"{request.user.employee_get} uploaded a document",
                    verb_ar=f"قام {request.user.employee_get} بتحميل مستند",
                    verb_de=f"{request.user.employee_get} hat ein Dokument hochgeladen",
                    verb_es=f"{request.user.employee_get} subió un documento",
                    verb_fr=f"{request.user.employee_get} a téléchargé un document",
                    redirect=reverse(
                        "employee-view-individual",
                        kwargs={"obj_id": request.user.employee_get.id},
                    ),
                    icon="chatbox-ellipses",
                )
            except:
                pass
            return HttpResponse("<script>window.location.reload();</script>")

    context = {"form": form, "document": document_item}
    return render(request, "tabs/htmx/document_form.html", context=context)



@login_required
@hx_request_required
def view_file(request, id):
    """
    This function used to view the uploaded document in the modal.
    Parameters:

    request (HttpRequest): The HTTP request object.
    id (int): The id of the document.

    Returns: return view_file template
    """

    document_obj = Document.objects.filter(id=id).first()
    context = {
        "document": document_obj,
    }
    if document_obj.document:
        file_path = document_obj.document.path
        file_extension = os.path.splitext(file_path)[1][
            1:
        ].lower()  # Get the lowercase file extension

        content_type = get_content_type(file_extension)

        try:
            with open(file_path, "rb") as file:
                file_content = file.read()  # Decode the binary content for display
        except:
            file_content = None

        context["file_content"] = file_content
        context["file_extension"] = file_extension
        context["content_type"] = content_type

    return render(request, "tabs/htmx/view_file.html", context)

@login_required
@hx_request_required
def view_incident_file(request, id):
    

    document_obj = EmployeeIncident.objects.filter(id=id).first()
    context = {
        "document": document_obj,
    }
    if document_obj.document:
        file_path = document_obj.document.path
        file_extension = os.path.splitext(file_path)[1][
            1:
        ].lower()  # Get the lowercase file extension

        content_type = get_content_type(file_extension)

        print(content_type, 'content', type (file_extension))




        try:
            with open(file_path, "rb") as file:
                file_content = file.read()  # Decode the binary content for display
        except:
            file_content = None

        context["file_content"] = file_content
        context["file_extension"] = file_extension
        context["content_type"] = content_type

    return render(request, "tabs/htmx/incident_file_view.html", context)


@login_required
def update_incident_document_title(request, id):
    
    document = get_object_or_404(EmployeeIncident, id=id)
    name = request.POST.get("title")
    if request.method == "POST":
        document.title = name
        document.save()
        messages.success(request, _("Incident title updated successfully"))
    else:
        messages.error(request, _("Invalid request"))
    return HttpResponse("")

@login_required
@hx_request_required
def incident_document_delete(request, id):
  
    try:
        document = EmployeeIncident.objects.filter(id=id)
        if not request.user.has_perm("aiz_documents.delete_document"):
            document = document.filter(
                employee_id__employee_user_id=request.user
            ).exclude(document_request_id__isnull=False)
        if document:
            document_first = document.first()
            document.delete()
            messages.success(
                request,
                _(
                    f"Incident request {document_first} for {document_first.employee_id} deleted successfully"
                ),
            )
            referrer = request.META.get("HTTP_REFERER", "")
            referrer = "/" + "/".join(referrer.split("/")[3:])
            if referrer.startswith("/employee/employee-view/") or referrer.endswith(
                "/employee/employee-profile/"
            ):
                existing_documents = EmployeeIncident.objects.filter(
                    employee_id=document_first.employee_id
                )
                if not existing_documents:
                    return HttpResponse(
                        f"""
                            <span hx-get='/employee/document-tab/{document_first.employee_id.id}?employee_view=true'
                            hx-target='#document_target' hx-trigger='load'></span>
                        """
                    )
            return HttpResponse()
        else:
            messages.error(request, _("Incident not found"))
    except ProtectedError:
        messages.error(request, _("You cannot delete this document."))
    return HttpResponse("<script>window.location.reload();</script>")

@login_required
@hx_request_required
def view_incident_file(request, id):
    

    document_obj = EmployeeIncident.objects.filter(id=id).first()
    context = {
        "document": document_obj,
    }
    if document_obj.document:
        file_path = document_obj.document.path
        file_extension = os.path.splitext(file_path)[1][
            1:
        ].lower()  # Get the lowercase file extension

        content_type = get_content_type(file_extension)

        try:
            with open(file_path, "rb") as file:
                file_content = file.read()  # Decode the binary content for display
        except:
            file_content = None

        context["file_content"] = file_content
        context["file_extension"] = file_extension
        context["content_type"] = content_type

    return render(request, "tabs/htmx/incident_file_view.html", context)



def get_content_type(file_extension):
    """
    This function retuns the content type of a file
    parameters:

    file_extension: The file extension of the file
    """

    content_types = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "jpg": "image/jpeg",
        "png": "image/png",
        "jpeg": "image/jpeg",
    }

    # Default to application/octet-stream if the file extension is not recognized
    return content_types.get(file_extension, "application/octet-stream")


@login_required
@hx_request_required
@manager_can_enter("aiz_documents.add_document")
def document_approve(request, id):
    """
    This function used to view the approve uploaded document.
    Parameters:

    request (HttpRequest): The HTTP request object.
    id (int): The id of the document.

    Returns:
    """

    document_obj = get_object_or_404(Document, id=id)
    if document_obj.document:
        document_obj.status = "approved"
        document_obj.save()
        messages.success(request, _("Document request approved"))
    else:
        messages.error(request, _("No document uploaded"))

    return HttpResponse("<script>window.location.reload();</script>")


@login_required
@hx_request_required
@manager_can_enter("aiz_documents.add_document")
def document_reject(request, id):
    """
    This function used to view the reject uploaded document.
    Parameters:

    request (HttpRequest): The HTTP request object.
    id (int): The id of the document.

    Returns:
    """
    document_obj = get_object_or_404(Document, id=id)
    form = DocumentRejectForm()
    if document_obj.document:
        if request.method == "POST":
            form = DocumentRejectForm(request.POST, instance=document_obj)
            if form.is_valid():
                test = form.save()
                document_obj.status = "rejected"
                document_obj.save()
                messages.error(request, _("Document request rejected"))

                return HttpResponse("<script>window.location.reload();</script>")
    else:
        messages.error(request, _("No document uploaded"))
        return HttpResponse("<script>window.location.reload();</script>")

    return render(
        request,
        "tabs/htmx/reject_form.html",
        {"form": form, "document_obj": document_obj},
    )


@login_required
@manager_can_enter("aiz_documents.add_document")
def document_bulk_approve(request):
    """
    This function used to view the approve uploaded document.
    Parameters:

    request (HttpRequest): The HTTP request object.

    Returns:
    """
    ids = request.GET.getlist("ids")
    document_obj = Document.objects.filter(
        id__in=ids,
    ).exclude(document="")
    document_obj.update(status="approved")
    messages.success(request, _(f"{len(document_obj)} Document request approved"))

    return HttpResponse("success")


@login_required
@manager_can_enter("aiz_documents.add_document")
def document_bulk_reject(request):
    """
    This function used to view the reject uploaded document.
    Parameters:

    request (HttpRequest): The HTTP request object.

    Returns:
    """
    ids = request.POST.getlist("ids")
    reason = request.POST.get("reason")
    document_obj = Document.objects.filter(id__in=ids)
    document_obj.update(status="rejected", reject_reason=reason)
    messages.success(request, _("Document request rejected"))
    return HttpResponse("success")


@login_required
@require_http_methods(["POST"])
def employee_profile_bank_details(request):
    """
    This method is used to fill self bank details
    """
    employee = request.user.employee_get
    instance = EmployeeBankDetails.objects.filter(employee_id=employee).first()
    form = EmployeeBankDetailsUpdateForm(request.POST, instance=instance)
    if form.is_valid():
        bank_info = form.save(commit=False)
        bank_info.employee_id = employee
        bank_info.save()
        messages.success(request, _("Bank details updated"))
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@login_required
@permission_required("employee.view_profile")
def employee_profile_update(request):
    """
    This method is used update own profile of the requested employee
    """

    employee_user = request.user
    employee = Employee.objects.get(employee_user_id=employee_user)
    if employee_user.has_perm("employee.change_profile"):
        if request.method == "POST":
            form = EmployeeForm(request.POST, request.FILES, instance=employee)
            if form.is_valid():
                form.save()
                messages.success(request, _("Profile updated."))
    return redirect("/employee/employee-profile")


@login_required
@permission_required("delete_group")
@require_http_methods(["POST"])
def employee_user_group_assign_delete(_, obj_id):
    """
    This method is used to delete user group assign
    """
    user = User.objects.get(id=obj_id)
    user.groups.clear()
    return redirect("/employee/employee-user-group-assign-view")


def paginator_qry(qryset, page_number):
    """
    This method is used to paginate query set
    """
    paginator = aizPaginator(qryset, get_pagination())
    qryset = paginator.get_page(page_number)
    return qryset


@login_required
@enter_if_accessible(
    feature="employee_view",
    perm="employee.view_employee",
    method=_check_reporting_manager,
)
def employee_view(request):
    """
    This method is used to render template for view all employee
    """
    view_type = request.GET.get("view")
    previous_data = request.GET.urlencode()
    page_number = request.GET.get("page")
    selected_company = request.session.get("selected_company")
    error_message = request.session.pop("error_message", None)
    queryset = (
        Employee.objects.filter(
            is_active=True, employee_work_info__company_id=selected_company
        )
        if selected_company != "all"
        else Employee.objects.filter(is_active=True)
    )

    filter_obj = EmployeeFilter(request.GET, queryset=queryset)
    update_fields = BulkUpdateFieldForm()
    data_dict = parse_qs(previous_data)
    get_key_instances(Employee, data_dict)
    emp = Employee.objects.filter()
    # calender = EventCalender.objects.all()

    # for time in calender:
    #     current_time = timezone.now()
    #     current_date = datetime.today()
    #     calculated_time = time.reminder_date - current_time
    #     # f (calculated_time < timedelta(minutes=60)) and (calculated_time > timedelta(minutes=55))
    #     if time.reminder_date == current_date:
    #         print(current_date, time.reminder_date)

    #         sender_email = "enamulcse12@gmail.com"
    #         receiver_email = "parvess1980@gmail.com"
    #         app_password = "iorg yewo vzwp gtgx" 


    #         subject = time.event_title
    #         body = "Hello, this is a test email sent from Python."
    #         email_body_html = f"""
    #             <html>
    #             <body>
    #                 <p>This is a reminder for an event <strong>{time.event_title}</strong>.</p>
    #                 <p>This is a Event Date <strong>{time.event_date}</strong>.</p>
    #                 <p>This is event Description <strong>{time.event_description}</strong>.</p>
    #             </body>
    #             </html>
    #             """
    #         # <p>Please join us at: <a href=""></a></p>
    #         # <p>Best regards,<br>Your Company Name</p>

    #         message = MIMEMultipart()
    #         message["From"] = sender_email
    #         message["To"] = receiver_email
    #         message["Subject"] = subject

    #         message.attach(MIMEText(email_body_html, "html"))

    #         try:
    #             server = smtplib.SMTP("smtp.gmail.com", 587)
    #             server.starttls()  # Secure the connection
    #             server.login(sender_email, app_password)
    #             server.sendmail(sender_email, receiver_email, message.as_string())
    #             print("Email sent successfully!")
    #         except Exception as e:
    #             print(f"Error sending email: {e}")
    #         finally:
    #             server.quit()


    # Store the employees in the session
    request.session["filtered_employees"] = [employee.id for employee in queryset]

    return render(
        request,
        "employee_personal_info/employee_view.html",
        {
            "data": paginator_qry(filter_obj.qs, page_number),
            "pd": previous_data,
            "f": filter_obj,
            "update_fields_form": update_fields,
            "view_type": view_type,
            "filter_dict": data_dict,
            "emp": emp,
            "gp_fields": EmployeeReGroup.fields,
            "error_message": error_message,
        },
    )


@login_required
@permission_required("employee.change_employee")
def view_employee_bulk_update(request):
    if request.method == "POST":
        update_fields = request.POST.getlist("update_fields")
        bulk_employee_ids = request.POST.get("bulk_employee_ids")
        bulk_employee_ids_str = (
            json.dumps(bulk_employee_ids) if bulk_employee_ids else ""
        )
        if bulk_employee_ids_str:

            class EmployeeBulkUpdateForm(ModelForm):
                class Meta:
                    model = Employee
                    fields = []
                    widgets = {}
                    labels = {}
                    for field in update_fields:
                        try:
                            field_obj = Employee._meta.get_field(field)
                            if field_obj.name in ("country", "state"):
                                if not "country" in update_fields:
                                    fields.append("country")
                                    widgets["country"] = Select(
                                        attrs={"required": True}
                                    )
                                fields.append(field)
                                widgets[field] = Select(attrs={"required": True})
                            else:
                                fields.append(field)

                            if isinstance(field_obj, models.DateField):
                                widgets[field] = DateInput(
                                    attrs={
                                        "type": "date",
                                        "required": True,
                                        "data-pp": False,
                                    }
                                )
                        except:
                            continue

                def __init__(self, *args, **kwargs):
                    super(EmployeeBulkUpdateForm, self).__init__(*args, **kwargs)
                    for field_name, field in self.fields.items():
                        field.required = True

            class WorkInfoBulkUpdateForm(ModelForm):
                class Meta:
                    model = EmployeeWorkInformation
                    fields = []
                    widgets = {}
                    labels = {}
                    for field in update_fields:
                        try:
                            parts = str(field).split("__")
                            if parts[-1]:
                                if parts[0] == "employee_work_info":
                                    field_obj = EmployeeWorkInformation._meta.get_field(
                                        parts[-1]
                                    )

                                    if (
                                        parts[1] == "department_id"
                                        or parts[1] == "job_position_id"
                                        or parts[1] == "job_role_id"
                                    ):
                                        if (
                                            not "employee_work_info__department_id"
                                            in update_fields
                                        ):
                                            fields.append("department_id")
                                            widgets["department_id"] = Select(
                                                attrs={"required": True}
                                            )
                                        if (
                                            not "employee_work_info__job_position_id"
                                            in update_fields
                                        ):
                                            fields.append("job_position_id")
                                            widgets["job_position_id"] = Select(
                                                attrs={"required": True}
                                            )
                                        if (
                                            not "employee_work_info__job_role_id"
                                            in update_fields
                                        ):
                                            fields.append("job_role_id")
                                            widgets["job_role_id"] = Select(
                                                attrs={"required": True}
                                            )
                                        fields.append(parts[1])
                                        widgets[field] = Select(
                                            attrs={"required": True}
                                        )

                                    fields.append(parts[-1])

                                    # Remove inner lists
                                    fields = [
                                        item
                                        for item in fields
                                        if not isinstance(item, list)
                                    ]

                                    if isinstance(field_obj, models.DateField):
                                        widgets[parts[-1]] = DateInput(
                                            attrs={"type": "date"}
                                        )
                                    if parts[-1] in ("email", "mobile"):
                                        labels[parts[-1]] = (
                                            _("Work Email")
                                            if field_obj.name == "email"
                                            else _("Work Phone")
                                        )
                        except:
                            continue

                def __init__(self, *args, **kwargs):
                    super(WorkInfoBulkUpdateForm, self).__init__(*args, **kwargs)
                    if "department_id" in self.fields:
                        self.fields["department_id"].widget.attrs.update(
                            {
                                "onchange": "depChange($(this))",
                            }
                        )
                    if "job_position_id" in self.fields:
                        self.fields["job_position_id"].widget.attrs.update(
                            {
                                "onchange": "jobChange($(this))",
                            }
                        )
                    for field_name, field in self.fields.items():
                        field.required = True

            class BankInfoBulkUpdateForm(ModelForm):
                class Meta:
                    model = EmployeeBankDetails
                    fields = []
                    widgets = {}
                    labels = {}
                    for field in update_fields:
                        try:
                            parts = str(field).split("__")
                            if parts[-1]:
                                if parts[0] == "employee_bank_details":
                                    field_obj = EmployeeBankDetails._meta.get_field(
                                        parts[-1]
                                    )
                                    fields.append(parts[-1])
                                    if isinstance(field_obj, models.DateField):
                                        widgets[parts[-1]] = DateInput(
                                            attrs={"type": "date"}
                                        )

                                    if field_obj.name in ("country", "state"):
                                        if not "country" in update_fields:
                                            fields.append("country")
                                            widgets["country"] = Select(
                                                attrs={"required": True}
                                            )
                                        fields.append(parts[-1])
                                        widgets[parts[-1]] = Select(
                                            attrs={"required": True}
                                        )
                                        labels[parts[-1]] = (
                                            _("Bank Country")
                                            if field_obj.name == "country"
                                            else _("Bank State")
                                        )

                        except:
                            continue

                def __init__(self, *args, **kwargs):
                    super(BankInfoBulkUpdateForm, self).__init__(*args, **kwargs)
                    for field_name, field in self.fields.items():
                        field.required = True

            form = EmployeeBulkUpdateForm()
            form1 = WorkInfoBulkUpdateForm()
            form2 = BankInfoBulkUpdateForm()

            keys = form1.fields.keys()
            # Convert dict_keys object to a list
            keys_list = list(keys)

            fields_list = []
            for i in keys_list:
                i = "employee_work_info__" + i
                fields_list.append(i)

            for i in fields_list:
                if i not in update_fields:
                    update_fields.append(i)

            update_fields_str = json.dumps(update_fields)

            context = {
                "form": form,
                "form1": form1,
                "form2": form2,
                "update_fields": update_fields_str,
                "bulk_employee_ids": bulk_employee_ids_str,
            }
            return render(
                request,
                "employee_personal_info/bulk_update.html",
                context=context,
            )
        else:
            messages.warning(
                request, _("There are no employees selected for bulk update.")
            )
            return redirect(employee_view)


@login_required
@permission_required("employee.change_employee")
def save_employee_bulk_update(request):
    if request.method == "POST":
        update_fields_str = request.POST.get("update_fields", "")
        update_fields = json.loads(update_fields_str) if update_fields_str else []
        dict_value = request.__dict__["_post"]
        bulk_employee_ids_str = request.POST.get("bulk_employee_ids", "")
        bulk_employee_ids = (
            json.loads(bulk_employee_ids_str) if bulk_employee_ids_str else []
        )
        employee_list = ast.literal_eval(bulk_employee_ids)
        for id in employee_list:
            try:
                employee_instance = Employee.objects.get(id=int(id))
                (
                    employee_work_info,
                    created,
                ) = EmployeeWorkInformation.objects.get_or_create(
                    employee_id=employee_instance
                )
                (
                    employee_bank,
                    created,
                ) = EmployeeBankDetails.objects.get_or_create(
                    employee_id=employee_instance
                )
            except (ValueError, OverflowError):
                employee_list.remove(id)
                pass
        for field in update_fields:
            parts = str(field).split("__")
            if parts[-1]:
                if parts[0] == "employee_work_info":
                    employee_queryset = EmployeeWorkInformation.objects.filter(
                        employee_id__in=employee_list
                    )
                    value = dict_value.get(parts[-1])
                    employee_queryset.update(**{parts[-1]: value})
                elif parts[0] == "employee_bank_details":
                    for id in employee_list:

                        employee_queryset = EmployeeBankDetails.objects.filter(
                            employee_id__in=employee_list
                        )
                        value = dict_value.get(parts[-1])
                        employee_queryset.update(**{parts[-1]: value})
                else:
                    employee_queryset = Employee.objects.filter(id__in=employee_list)
                    value = dict_value.get(field)
                    employee_queryset.update(**{field: value})
        if len(employee_list) > 0:
            messages.success(
                request,
                _(
                    "{} employees information updated successfully".format(
                        len(employee_list)
                    )
                ),
            )
    return redirect("/employee/employee-view/?view=list")


@login_required
@permission_required("employee.change_employee")
def employee_account_block_unblock(request, emp_id):
    employee = get_object_or_404(Employee, id=emp_id)
    if not employee:
        messages.info(request, _("Employee not found"))
        return redirect(employee_view)
    user = get_object_or_404(User, id=employee.employee_user_id.id)
    if not user:
        messages.info(request, _("Employee not found"))
        return redirect(employee_view)
    if not user.is_superuser:
        user.is_active = not user.is_active
        action_message = _("blocked") if not user.is_active else _("unblocked")
        user.save()
        messages.success(
            request,
            _("{employee}'s account {action_message} successfully!").format(
                employee=employee, action_message=action_message
            ),
        )
    else:
        messages.info(
            request,
            _("{employee} is a superuser and cannot be blocked.").format(
                employee=employee
            ),
        )
    return redirect(employee_view_individual, obj_id=emp_id)


@login_required
@permission_required("employee.add_employee")
def employee_view_new(request):
    """
    This method is used to render form to create a new employee.
    """
    form = EmployeeForm()
    work_form = EmployeeWorkInformationForm()
    bank_form = EmployeeBankDetailsForm()
    filter_obj = EmployeeFilter(queryset=Employee.objects.all())
    return render(
        request,
        "employee/create_form/form_view.html",
        {"form": form, "work_form": work_form, "bank_form": bank_form, "f": filter_obj},
    )


@login_required
@manager_can_enter("employee.change_employee")
def employee_view_update(request, obj_id, **kwargs):
    """
    This method is used to render update form for employee.
    """
    company = request.session["selected_company"]
    user = Employee.objects.filter(employee_user_id=request.user).first()
    work_info = HistoryTrackingFields.objects.first()
    print(work_info, 'work')
    work_info_history = False
    if work_info and work_info.work_info_track == True:
        work_info_history = True

    employee = Employee.objects.filter(id=obj_id).first()
    all_employees = Employee.objects.get_all()
    emp = all_employees.filter(id=obj_id).first()
    if employee is None:
        employee = emp
        all_work_info = EmployeeWorkInformation.objects.get_all()
        cmpny = Company.objects.get(id=company)
        work = all_work_info.filter(employee_id=employee).first()
        if company != "all":
            work.company_id = cmpny
            work.save()
        employee.save()

    if (
        user
        and user.reporting_manager.filter(employee_id=employee).exists()
        or request.user.has_perm("employee.change_employee")
    ):
        form = EmployeeForm(instance=employee)
        work_form = EmployeeWorkInformationForm(
            instance=EmployeeWorkInformation.objects.filter(
                employee_id=employee
            ).first()
        )
        bank_form = EmployeeBankDetailsForm(
            instance=EmployeeBankDetails.objects.filter(employee_id=employee).first()
        )
        if request.POST:
            if request.POST.get("form") == "personal":
                form = EmployeeForm(request.POST, instance=employee)
                if form.is_valid():
                    form.save()
                    messages.success(
                        request, _("Employee personal information updated.")
                    )
            elif request.POST.get("form") == "work":
                instance = EmployeeWorkInformation.objects.filter(
                    employee_id=employee
                ).first()
                work_form = EmployeeWorkInformationUpdateForm(
                    request.POST, instance=instance
                )
                if work_form.is_valid():
                    instance = work_form.save(commit=False)
                    instance.employee_id = employee
                    instance.save()
                    instance.tags.set(request.POST.getlist("tags"))
                    notify.send(
                        request.user.employee_get,
                        recipient=instance.employee_id.employee_user_id,
                        verb="Your work details has been updated.",
                        verb_ar="تم تحديث تفاصيل عملك.",
                        verb_de="Ihre Arbeitsdetails wurden aktualisiert.",
                        verb_es="Se han actualizado los detalles de su trabajo.",
                        verb_fr="Vos informations professionnelles ont été mises à jour.",
                        redirect=reverse("employee-profile"),
                        icon="briefcase",
                    )
                    messages.success(request, _("Employee work information updated."))
                work_form = EmployeeWorkInformationForm(
                    instance=EmployeeWorkInformation.objects.filter(
                        employee_id=employee
                    ).first()
                )
            elif request.POST.get("form") == "bank":
                instance = EmployeeBankDetails.objects.filter(
                    employee_id=employee
                ).first()
                bank_form = EmployeeBankDetailsUpdateForm(
                    request.POST, instance=instance
                )
                if bank_form.is_valid():
                    instance = bank_form.save(commit=False)
                    instance.employee_id = employee
                    instance.save()
                    messages.success(request, _("Employee bank details updated."))

        job_experiences = EmployeeJobExperiences.objects.filter(employee_id=employee)
        employee_educations = EmployeeEducation.objects.filter(employee_id=employee)
        employee_trainings = EmployeeTraining.objects.filter(employee_id=employee)
        job_refers = JobReference.objects.filter(employee_id=employee)
        documents = Document.objects.filter(employee_id=employee)
        return render(
            request,
            "employee/update_form/form_view.html",
            {
                "obj_id": obj_id,
                "form": form,
                "work_form": work_form,
                "bank_form": bank_form,
                "work_info_history": work_info_history,
                "job_experiences": job_experiences,
                "employee_educations": employee_educations,
                "employee_trainings": employee_trainings,
                "job_refers": job_refers,
                "documents" : documents
            },
        )
    return HttpResponseRedirect(
        request.META.get("HTTP_REFERER", "/employee/employee-view")
    )


@login_required
@require_http_methods(["POST"])
@permission_required("employee.change_employee")
def update_profile_image(request, obj_id):
    """
    This method is used to upload a profile image
    """
    try:
        employee = Employee.objects.get(id=obj_id)
        img = request.FILES["employee_profile"]
        employee.employee_profile = img
        employee.save()
        messages.success(request, _("Profile image updated."))
    except Exception:
        messages.error(request, _("No image chosen."))
    response = render(
        request,
        "employee/profile/profile_modal.html",
    )
    return HttpResponse(
        response.content.decode("utf-8") + "<script>location.reload();</script>"
    )


@login_required
@require_http_methods(["POST"])
def update_own_profile_image(request):
    """
    This method is used to update own profile image from profile view form
    """
    employee = request.user.employee_get
    img = request.FILES.get("employee_profile")
    employee.employee_profile = img
    employee.save()
    messages.success(request, _("Profile image updated."))
    response = render(
        request,
        "employee/profile/profile_modal.html",
    )
    return HttpResponse(
        response.content.decode("utf-8") + "<script>location.reload();</script>"
    )


@login_required
@require_http_methods(["DELETE"])
@permission_required("employee.change_employee")
def remove_profile_image(request, obj_id):
    """
    This method is used to remove uploaded image
    Args: obj_id : Employee model instance id
    """
    employee = Employee.objects.get(id=obj_id)
    if employee.employee_profile.name == "":
        messages.info(request, _("No profile image to remove."))
        response = render(
            request,
            "employee/profile/profile_modal.html",
        )
        return HttpResponse(
            response.content.decode("utf-8") + "<script>location.reload();</script>"
        )
    file_path = employee.employee_profile.path
    absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
    os.remove(absolute_path)
    employee.employee_profile = None
    employee.save()
    messages.success(request, _("Profile image removed."))
    response = render(
        request,
        "employee/profile/profile_modal.html",
    )
    return HttpResponse(
        response.content.decode("utf-8") + "<script>location.reload();</script>"
    )


@login_required
@require_http_methods(["DELETE"])
def remove_own_profile_image(request):
    """
    This method is used to remove own profile image
    """
    employee = request.user.employee_get
    if employee.employee_profile.name == "":
        messages.info(request, _("No profile image to remove."))
        response = render(
            request,
            "employee/profile/profile_modal.html",
        )
        return HttpResponse(
            response.content.decode("utf-8") + "<script>location.reload();</script>"
        )
    file_path = employee.employee_profile.path
    absolute_path = os.path.join(settings.MEDIA_ROOT, file_path)
    os.remove(absolute_path)
    employee.employee_profile = None
    employee.save()

    messages.success(request, _("Profile image removed."))
    response = render(
        request,
        "employee/profile/profile_modal.html",
    )
    return HttpResponse(
        response.content.decode("utf-8") + "<script>location.reload();</script>"
    )


@login_required
@manager_can_enter("employee.change_employee")
@require_http_methods(["POST"])
def employee_create_update_personal_info(request, obj_id=None):
    """
    This method is used to update employee's personal info.
    """
    employee = Employee.objects.filter(id=obj_id).first()
    form = EmployeeForm(request.POST, instance=employee)
    if form.is_valid():
        form.save()
        if obj_id is None:
            messages.success(request, _("New Employee Added."))
            form = EmployeeForm(request.POST, instance=form.instance)
            work_form = EmployeeWorkInformationForm(
                instance=EmployeeWorkInformation.objects.filter(
                    employee_id=employee
                ).first()
            )
            bank_form = EmployeeBankDetailsForm(
                instance=EmployeeBankDetails.objects.filter(
                    employee_id=employee
                ).first()
            )
            return redirect(
                f"employee-view-update/{form.instance.id}/",
                data={"form": form, "work_form": work_form, "bank_form": bank_form},
            )
        return HttpResponse(
            """
                <div class="oh-alert-container">
                    <div class="oh-alert oh-alert--animated oh-alert--success">
                        Personal Info updated
                    </div>
                </div>

        """
        )
    if obj_id is None:
        return render(
            request,
            "employee/create_form/form_view.html",
            {
                "form": form,
            },
        )
    errors = "\n".join(
        [
            f"<li>{form.fields.get(field, field).label}: {', '.join(errors)}</li>"
            for field, errors in form.errors.items()
        ]
    )
    return HttpResponse(f'<ul class="alert alert-danger">{errors}</ul>')


@login_required
@manager_can_enter("employee.change_employeeworkinformation")
@require_http_methods(["POST"])
def employee_update_work_info(request, obj_id=None):
    """
    This method is used to update employee work info
    """
    employee = Employee.objects.filter(id=obj_id).first()
    form = EmployeeWorkInformationForm(
        request.POST,
        instance=EmployeeWorkInformation.objects.filter(employee_id=employee).first(),
    )
    form.fields["employee_id"].required = False
    form.employee_id = employee
    if form.is_valid() and employee is not None:
        work_info = form.save(commit=False)
        work_info.employee_id = employee
        work_info.save()
        return HttpResponse(
            """

                <div class="oh-alert-container">
                    <div class="oh-alert oh-alert--animated oh-alert--success">
                        Personal Info updated
                    </div>
                </div>

        """
        )
    errors = "\n".join(
        [
            f"<li>{form.fields.get(field, field).label}: {', '.join(errors)}</li>"
            for field, errors in form.errors.items()
        ]
    )
    return HttpResponse(f'<ul class="alert alert-danger">{errors}</ul>')


@login_required
@manager_can_enter("employee.change_employeebankdetails")
@require_http_methods(["POST"])
def employee_update_bank_details(request, obj_id=None):
    """
    This method is used to render form to create employee's bank information.
    """
    employee = Employee.objects.filter(id=obj_id).first()
    form = EmployeeBankDetailsForm(
        request.POST,
        instance=EmployeeBankDetails.objects.filter(employee_id=employee).first(),
    )
    if form.is_valid() and employee is not None:
        bank_info = form.save(commit=False)
        bank_info.employee_id = employee
        bank_info.save()
        return HttpResponse(
            """
            <div class="oh-alert-container">
                <div class="oh-alert oh-alert--animated oh-alert--success">
                    Bank details updated
                </div>
            </div>
        """
        )
    errors = "\n".join(
        [
            f"<li>{form.fields.get(field, field).label}: {', '.join(errors)}</li>"
            for field, errors in form.errors.items()
        ]
    )
    return HttpResponse(f'<ul class="alert alert-danger">{errors}</ul>')


@login_required
@hx_request_required
@enter_if_accessible(
    feature="employee_view",
    perm="employee.view_employee",
    method=_check_reporting_manager,
)
def employee_filter_view(request):
    """
    This method is used to filter employee.
    """
    previous_data = request.GET.urlencode()
    field = request.GET.get("field")
    queryset = Employee.objects.filter()
    selected_company = request.session.get("selected_company")
    employees = EmployeeFilter(request.GET, queryset=queryset).qs
    if request.GET.get("is_active") != "False":
        employees = employees.filter(is_active=True)
    if (
        request.GET.get("employee_work_info__company_id") == None
        and selected_company != "all"
    ):
        employees = employees.filter(employee_work_info__company_id=selected_company)
    page_number = request.GET.get("page")
    view = request.GET.get("view")
    data_dict = parse_qs(previous_data)
    get_key_instances(Employee, data_dict)
    template = "employee_personal_info/employee_card.html"
    if view == "list":
        template = "employee_personal_info/employee_list.html"
    if field != "" and field is not None:
        employees = group_by_queryset(employees, field, page_number, "page")
        template = "employee_personal_info/group_by.html"
    else:
        employees = sortby(request, employees, "orderby")
        employees = paginator_qry(employees, page_number)

        # Store the employees in the session
        request.session["filtered_employees"] = [employee.id for employee in employees]

    return render(
        request,
        template,
        {
            "data": employees,
            "f": EmployeeFilter(request.GET),
            "pd": previous_data,
            "field": field,
            "filter_dict": data_dict,
        },
    )


@login_required
@manager_can_enter("employee.view_employee")
@hx_request_required
def employee_card(request):
    """
    This method renders card template to view all employees.
    """
    previous_data = request.GET.urlencode()
    search = request.GET.get("search")
        

    if isinstance(search, type(None)):
        search = ""
    employees = filtersubordinatesemployeemodel(
        request, Employee.objects.all(), "employee.view_employee"
    )
    if request.GET.get("is_active") is None:
        filter_obj = EmployeeFilter(
            request.GET,
            queryset=employees.filter(
                employee_first_name__icontains=search, is_active=True
            ),
        )
    else:
        filter_obj = EmployeeFilter(
            request.GET,
            queryset=employees.filter(employee_first_name__icontains=search),
        )
    page_number = request.GET.get("page")
    employees = sortby(request, filter_obj.qs, "orderby")
    return render(
        request,
        "employee_personal_info/employee_card.html",
        {
            "data": paginator_qry(employees, page_number),
            "f": filter_obj,
            "pd": previous_data,
        },
    )


@login_required
@manager_can_enter("employee.view_employee")
@hx_request_required
def employee_list(request):
    """
    This method renders template to view all employees
    """
    previous_data = request.GET.urlencode()
    search = request.GET.get("search")
    if isinstance(search, type(None)):
        search = ""
    if request.GET.get("is_active") is None:
        filter_obj = EmployeeFilter(
            request.GET,
            queryset=Employee.objects.filter(
                employee_first_name__icontains=search, is_active=True
            ),
        )
    else:
        filter_obj = EmployeeFilter(
            request.GET,
            queryset=Employee.objects.filter(employee_first_name__icontains=search),
        )
    employees = filtersubordinatesemployeemodel(
        request, filter_obj.qs, "employee.view_employee"
    )
    employees = sortby(request, employees, "orderby")
    page_number = request.GET.get("page")
    return render(
        request,
        "employee_personal_info/employee_list.html",
        {
            "data": paginator_qry(employees, page_number),
            "f": filter_obj,
            "pd": previous_data,
        },
    )


@login_required
@hx_request_required
@manager_can_enter("employee.view_employee")
def employee_update(request, obj_id):
    """
    This method is used to update employee if the form is valid
    args:
        obj_id : employee id
    """
    employee = Employee.objects.get(id=obj_id)
    form = EmployeeForm(instance=employee)
    work_info = EmployeeWorkInformation.objects.filter(employee_id=employee).first()
    bank_info = EmployeeBankDetails.objects.filter(employee_id=employee).first()
    work_form = EmployeeWorkInformationForm()
    bank_form = EmployeeBankDetailsUpdateForm()
    if work_info is not None:
        work_form = EmployeeWorkInformationForm(instance=work_info)
    if bank_info is not None:
        bank_form = EmployeeBankDetailsUpdateForm(instance=bank_info)
    if request.method == "POST":
        if request.user.has_perm("employee.change_employee"):
            form = EmployeeForm(request.POST, request.FILES, instance=employee)
            if form.is_valid():
                form.save()
                messages.success(request, _("Employee updated."))
    return render(
        request,
        "employee_personal_info/employee_update_form.html",
        {"form": form, "work_form": work_form, "bank_form": bank_form},
    )


@login_required
@permission_required("employee.delete_employee")
@require_http_methods(["POST"])
def employee_delete(request, obj_id):
    """
    This method is used to delete employee
    args:
        id  : employee id
    """

    try:
        view = request.POST.get("view")
        employee = Employee.objects.get(id=obj_id)
        if apps.is_installed("payroll"):
            if employee.contract_set.all().exists():
                contracts = employee.contract_set.all()
                for contract in contracts:
                    if contract.contract_status != "active":
                        contract.delete()
        user = employee.employee_user_id
        try:
            user.delete()
        except AttributeError:
            employee.delete()
        messages.success(request, _("Employee deleted"))

    except Employee.DoesNotExist:
        messages.error(request, _("Employee not found."))
    except ProtectedError as e:
        model_verbose_names_set = set()
        for obj in e.protected_objects:
            model_verbose_names_set.add(__(obj._meta.verbose_name.capitalize()))
        model_names_str = ", - ".join(model_verbose_names_set)
        error_message = _("- {}.".format(model_names_str))
        error_message = str(error_message)
        request.session["error_message"] = error_message
        return redirect(employee_view)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", f"/view={view}"))


@login_required
@permission_required("employee.delete_employee")
def employee_bulk_delete(request):
    """
    This method is used to delete set of Employee instances
    """
    ids = request.POST["ids"]
    ids = json.loads(ids)
    for employee_id in ids:
        try:
            employee = Employee.objects.get(id=employee_id)
            if apps.is_installed("payroll"):
                if employee.contract_set.all().exists():
                    contracts = employee.contract_set.all()
                    for contract in contracts:
                        if contract.contract_status != "active":
                            contract.delete()
            user = employee.employee_user_id
            user.delete()
            messages.success(
                request, _("%(employee)s deleted.") % {"employee": employee}
            )
        except Employee.DoesNotExist:
            messages.error(request, _("Employee not found."))
        except ProtectedError:
            messages.error(
                request, _("You cannot delete %(employee)s.") % {"employee": employee}
            )

    return JsonResponse({"message": "Success"})


@login_required
@permission_required("employee.delete_employee")
@require_http_methods(["POST"])
def employee_bulk_archive(request):
    """
    This method is used to archive bulk of Employee instances
    """
    ids = request.POST["ids"]
    ids = json.loads(ids)
    is_active = False
    if request.GET.get("is_active") == "True":
        is_active = True
    for employee_id in ids:
        employee = Employee.objects.get(id=employee_id)

        emp = Employee.objects.get(id=employee_id)
        if emp.employee_user_id.is_superuser and emp.is_active:
            count = 0
            employees = Employee.objects.filter(is_active=True)
            for super_emp in employees:
                if super_emp.employee_user_id.is_superuser:
                    count = count + 1
            if count == 1:
                messages.error(request, _("You can't archive the last superuser."))
                return HttpResponse("<script>$('#filterEmployee').click();</script>")

        employee.is_active = is_active
        employee.employee_user_id.is_active = is_active
        if employee.get_archive_condition() is False:
            employee.save()
            message = _("archived")
            if is_active:
                message = _("un-archived")
            messages.success(request, f"{employee} is {message}")
        else:
            messages.warning(request, _("Related data found for {}.").format(employee))
    return JsonResponse({"message": "Success"})


@login_required
@hx_request_required
@permission_required("employee.delete_employee")
def employee_archive(request, obj_id):
    """
    This method is used to archive employee instance
    Args:
            obj_id : Employee instance id
    """
    employee = Employee.objects.get(id=obj_id)
    employee.is_active = not employee.is_active
    employee.employee_user_id.is_active = not employee.is_active
    save = True
    message = "Employee un-archived"
    if not employee.is_active:

        emp = Employee.objects.get(id=obj_id)
        if emp.employee_user_id.is_superuser:
            count = 0
            employees = Employee.objects.filter(is_active=True)
            for super_emp in employees:
                if super_emp.employee_user_id.is_superuser:
                    count = count + 1
            if count == 1:
                messages.error(request, _("You can't archive the last superuser."))
                return HttpResponse("<script>$('#filterEmployee').click();</script>")

        result = employee.get_archive_condition()
        if result:
            save = False
        else:
            message = _("Employee archived")
    if save:
        employee.save()
        messages.success(request, message)
        key = "HTTP_HX_REQUEST"
        if key not in request.META.keys():
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        else:
            return HttpResponse("<script>$('#filterEmployee').click();</script>")
    else:
        return render(
            request,
            "related_models.html",
            {
                "employee": employee,
                "related_models": result.get("related_models"),
                "related_model_fields": result.get("related_model_fields"),
                "employee_choices": result.get("employee_choices"),
                "title": _("Can't Archive"),
            },
        )


@login_required
@permission_required("employee.change_employee")
def replace_employee(request, emp_id):
    title = request.GET.get("title")
    employee = Employee.objects.filter(id=emp_id).first()
    related_models = (
        employee.get_archive_condition().get("related_models", "") if employee else None
    )
    if related_models and employee:
        for models in related_models:
            field_name = models.get("field_name", "")
            if field_name:
                replace_emp_id = request.POST.get(field_name)
                replace_emp = Employee.objects.filter(id=replace_emp_id).first()
                if (
                    field_name == "reporting_manager_id"
                    and str(emp_id) != replace_emp_id
                ):
                    reporting_manager = EmployeeWorkInformation.objects.filter(
                        reporting_manager_id=emp_id
                    ).update(reporting_manager_id=replace_emp)
                elif (
                    apps.is_installed("recruitment")
                    and field_name == "recruitment_managers"
                    and str(emp_id) != replace_emp_id
                ):
                    Recruitment = get_aiz_model_class(
                        app_label="recruitment", model="recruitment"
                    )
                    recruitment_query = Recruitment.objects.filter(
                        recruitment_managers=emp_id
                    )
                    if recruitment_query:
                        for recruitment in recruitment_query:
                            recruitment.recruitment_managers.remove(emp_id)
                            recruitment.recruitment_managers.add(replace_emp)
                elif (
                    apps.is_installed("recruitment")
                    and field_name == "recruitment_stage_managers"
                    and str(emp_id) != replace_emp_id
                ):
                    Stage = get_aiz_model_class(
                        app_label="recruitment", model="stage"
                    )
                    recruitment_stage_query = Stage.objects.filter(
                        stage_managers=emp_id
                    )
                    if recruitment_stage_query:
                        for stage in recruitment_stage_query:
                            stage.stage_managers.remove(emp_id)
                            stage.stage_managers.add(replace_emp)
                elif (
                    apps.is_installed("onboarding")
                    and field_name == "onboarding_stage_manager"
                    and str(emp_id) != replace_emp_id
                ):
                    OnboardingStage = get_aiz_model_class(
                        app_label="onboarding", model="onboardingstage"
                    )
                    onboarding_stage_query = OnboardingStage.objects.filter(
                        employee_id=emp_id
                    )
                    if onboarding_stage_query:
                        for stage in onboarding_stage_query:
                            stage.employee_id.remove(emp_id)
                            stage.employee_id.add(replace_emp)
                elif (
                    apps.is_installed("onboarding")
                    and field_name == "onboarding_task_manager"
                    and str(emp_id) != replace_emp_id
                ):
                    OnboardingTask = get_aiz_model_class(
                        app_label="onboarding", model="onboardingtask"
                    )
                    onboarding_task_query = OnboardingTask.objects.filter(
                        employee_id=emp_id
                    )
                    if onboarding_task_query:
                        for task in onboarding_task_query:
                            task.employee_id.remove(emp_id)
                            task.employee_id.add(replace_emp)
                else:
                    pass
    related_models = employee.get_archive_condition()
    if title == "Change the Designations":
        messages.success(request, _("Designation changed."))
        return redirect("/offboarding/offboarding-pipeline")
    if related_models is False and title != "Change the Designations":
        employee.is_active = False
        employee.save()
        messages.success(request, _("{} archived successfully").format(employee))
    return redirect(employee_view)


@login_required
@permission_required("employee.view_employee")
def get_manager_in(request):
    """
    This method is used to get the manager in records model
    """
    employee_id = request.GET.get("employee_id")
    employee = Employee.objects.filter(id=employee_id).first()
    offboarding = request.GET.get("offboarding")
    if offboarding:
        title = _("Change the Designations")
    else:
        title = _("Can't Archive")
    employee.is_active = not employee.is_active
    employee.employee_user_id.is_active = not employee.is_active
    save = True
    message = "Employee un-archived"
    if not employee.is_active:
        result = employee.get_archive_condition()
        if result:
            save = False
        else:
            message = _("Employee archived")
    if save:
        employee.save()
        messages.success(request, message)
        key = "HTTP_HX_REQUEST"
        if key not in request.META.keys():
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        else:
            return HttpResponse("<script>window.location.reload()</script>")
    else:
        return render(
            request,
            "related_models.html",
            {
                "employee": employee,
                "related_models": result.get("related_models"),
                "related_model_fields": result.get("related_model_fields"),
                "employee_choices": result.get("employee_choices"),
                "title": title,
            },
        )


@login_required
@enter_if_accessible(
    feature="employee_view",
    perm="employee.view_employee",
    method=_check_reporting_manager,
)
def employee_search(request):
    """
    This method is used to search employee
    """
    search = request.GET["search"]
    view = request.GET["view"]
    previous_data = request.GET.urlencode()
    employees = EmployeeFilter(request.GET).qs
    if search == "":
        employees = employees.filter(is_active=True)
    page_number = request.GET.get("page")
    template = "employee_personal_info/employee_card.html"
    if view == "list":
        template = "employee_personal_info/employee_list.html"
    employees = filtersubordinatesemployeemodel(
        request, employees, "employee.view_employee"
    )
    employees = sortby(request, employees, "orderby")
    data_dict = parse_qs(previous_data)
    get_key_instances(Employee, data_dict)
    return render(
        request,
        template,
        {
            "data": paginator_qry(employees, page_number),
            "pd": previous_data,
            "filter_dict": data_dict,
        },
    )


@login_required
@manager_can_enter("employee.add_employeeworkinformation")
@require_http_methods(["POST"])
def employee_work_info_view_create(request, obj_id):
    """
    This method is used to create employee work information from employee single view template
    args:
        obj_id : employee instance id
    """

    employee = Employee.objects.get(id=obj_id)
    form = EmployeeForm(instance=employee)

    work_form = EmployeeWorkInformationUpdateForm(request.POST)

    bank_form = EmployeeBankDetailsUpdateForm()
    bank_form_instance = EmployeeBankDetails.objects.filter(
        employee_id=employee
    ).first()
    if bank_form_instance is not None:
        bank_form = EmployeeBankDetailsUpdateForm(
            instance=employee.employee_bank_details
        )

    if work_form.is_valid():
        work_info = work_form.save(commit=False)
        work_info.employee_id = employee
        work_info.save()
        messages.success(request, _("Created work information"))
    return render(
        request,
        "employee_personal_info/employee_update_form.html",
        {"form": form, "work_form": work_form, "bank_form": bank_form},
    )


@login_required
@manager_can_enter("employee.change_employeeworkinformation")
@require_http_methods(["POST"])
def employee_work_info_view_update(request, obj_id):
    """
    This method is used to update employee work information from single view template
    args:
        obj_id  : employee work information id
    """

    work_information = EmployeeWorkInformation.objects.get(id=obj_id)
    form = EmployeeForm(instance=work_information.employee_id)
    bank_form = EmployeeBankDetailsUpdateForm(
        instance=work_information.employee_id.employee_bank_details
    )
    work_form = EmployeeWorkInformationUpdateForm(
        request.POST,
        instance=work_information,
    )
    if work_form.is_valid():
        work_form.save()
        messages.success(request, _("Work Information Updated Successfully"))
    return render(
        request,
        "employee_personal_info/employee_update_form.html",
        {"form": form, "work_form": work_form, "bank_form": bank_form},
    )


@login_required
@manager_can_enter("employee.add_employeebankdetails")
@require_http_methods(["POST"])
def employee_bank_details_view_create(request, obj_id):
    """
    This method used to create bank details object from the view template
    args:
        obj_id : employee instance id
    """
    employee = Employee.objects.get(id=obj_id)
    form = EmployeeForm(instance=employee)
    bank_form = EmployeeBankDetailsUpdateForm(request.POST)
    work_form_instance = EmployeeWorkInformation.objects.filter(
        employee_id=employee
    ).first()
    work_form = EmployeeWorkInformationUpdateForm()
    if work_form_instance is not None:
        work_form = EmployeeWorkInformationUpdateForm(instance=work_form_instance)
    if bank_form.is_valid():
        bank_instance = bank_form.save(commit=False)
        bank_instance.employee_id = employee
        bank_instance.save()
        messages.success(request, _("Bank Details Created Successfully"))
    return render(
        request,
        "employee_personal_info/employee_update_form.html",
        {"form": form, "work_form": work_form, "bank_form": bank_form},
    )


@login_required
@manager_can_enter("employee.change_employeebankdetails")
@require_http_methods(["POST"])
def employee_bank_details_view_update(request, obj_id):
    """
    This method is used to update employee bank details.
    """
    employee_bank_instance = EmployeeBankDetails.objects.get(id=obj_id)
    form = EmployeeForm(instance=employee_bank_instance.employee_id)
    work_form = EmployeeWorkInformationUpdateForm(
        instance=employee_bank_instance.employee_id.employee_work_info
    )
    bank_form = EmployeeBankDetailsUpdateForm(
        request.POST, instance=employee_bank_instance
    )
    if bank_form.is_valid():
        bank_instance = bank_form.save(commit=False)
        bank_instance.employee_id = employee_bank_instance.employee_id
        bank_instance.save()
        messages.success(request, _("Bank Details Updated Successfully"))
    return render(
        request,
        "employee_personal_info/employee_update_form.html",
        {"form": form, "work_form": work_form, "bank_form": bank_form},
    )


@login_required
@permission_required("employee.delete_employeeworkinformation")
@require_http_methods(["POST", "DELETE"])
def employee_work_information_delete(request, obj_id):
    """
    This method is used to delete employee work information
    args:
        obj_id : employee work information id
    """
    try:
        employee_work = EmployeeWorkInformation.objects.get(id=obj_id)
        employee_work.delete()
        messages.success(request, _("Employee work information deleted"))
    except EmployeeWorkInformation.DoesNotExist:
        messages.error(request, _("Employee work information not found."))
    except ProtectedError:
        messages.error(request, _("You cannot delete this Employee work information"))

    return redirect("/employee/employee-work-information-view")


@login_required
@permission_required("employee.add_employee")
def employee_import(request):
    """
    This method is used to create employee and corresponding user.
    """
    if request.method == "POST":
        file = request.FILES["file"]
        # Read the Excel file into a Pandas DataFrame
        data_frame = pd.read_excel(file)
        # Convert the DataFrame to a list of dictionaries
        employee_dicts = data_frame.to_dict("records")
        # Create or update Employee objects from the list of dictionaries
        error_list = []
        for employee_dict in employee_dicts:
            try:
                phone = employee_dict["phone"]
                email = employee_dict["email"]
                employee_full_name = employee_dict["employee_full_name"]
                existing_user = User.objects.filter(username=email).first()
                if existing_user is None:
                    employee_first_name = employee_full_name
                    employee_last_name = ""
                    if " " in employee_full_name:
                        (
                            employee_first_name,
                            employee_last_name,
                        ) = employee_full_name.split(" ", 1)

                    user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=str(phone).strip(),
                        is_superuser=False,
                    )
                    employee = Employee()
                    employee.employee_user_id = user
                    employee.employee_first_name = employee_first_name
                    employee.employee_last_name = employee_last_name
                    employee.email = email
                    employee.phone = phone
                    employee.save()
            except Exception:
                error_list.append(employee_dict)
        return HttpResponse(
            """
    <div class='alert-success p-3 border-rounded'>
        Employee data has been imported successfully.
    </div>

    """
        )
    data_frame = pd.DataFrame(columns=["employee_full_name", "email", "phone"])
    # Export the DataFrame to an Excel file
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="employee_template.xlsx"'
    data_frame.to_excel(response, index=False)
    return response


@login_required
@permission_required("employee.add_employee")
def employee_export(_):
    """
    This method is used to export employee data to xlsx
    """
    # Get the list of field names for your model
    field_names = [f.name for f in Employee._meta.get_fields() if not f.auto_created]
    field_names.remove("employee_user_id")
    field_names.remove("employee_profile")
    field_names.remove("additional_info")
    field_names.remove("is_from_onboarding")
    field_names.remove("is_directly_converted")
    field_names.remove("is_active")

    # Get the existing employee data and convert it to a DataFrame
    employee_data = Employee.objects.values_list(*field_names)
    data_frame = pd.DataFrame(list(employee_data), columns=field_names)

    # Export the DataFrame to an Excel file

    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="employee_export.xlsx"'
    data_frame.to_excel(response, index=False)

    return response


def convert_nan(field, dicts):
    """
    This method is returns None or field value
    """
    field_value = dicts.get(field)
    try:
        float(field_value)
        return None
    except ValueError:
        return field_value

  

@login_required
@permission_required("employee.add_employee")
def work_info_import(request):
    """
    This method is used to import Employee instances and creates related objects
    """
    data_frame = pd.DataFrame(
        columns=[
            "Employee ID",
            "First Name",
            "Last Name",
            "Job Position",
            "Employee Grade",
            "Department",
            "Employee Section",
            "Reporting Manager",
            "Employee Unit",
            "Employee Category",
            "Date Of Joining",
            "Last Promotion Date",
            "Casual ID for Casual Employee",
            "Joining date for Casual Employee",
            "Payroll Enrollment date for Casual Employee",
            "Service Length In Incepta",
            "Date of Birth",
            "Job Experience 1",
            "Job Experience 2",
            "Job Experience 3",
            "Job Experience 4",
            "Graduation Subject",
            "Graduation University",
            "Post Graduation Subject",
            "Post Graduation University",
            "Highest Educational Degree",
            "Professional Degree or Specialized Training",
            "Job Reference",
            "Employee Contact Number (Official)",
            "Employee Contact Number (Personal)",
            "Emergency Contact Number",
            "Employee Email(Official)",
            "Employee Email(Personal)",
            "Employee Gender",
            "Employee Blood Group",
            "Employee Religion",
            "Employee Father's Name (According to NID)",
            "Employee Mother's Name (According to NID)",
            "Employee Marital Status",
            "Employee Spouse Name (According to NID)_If Married",
            "Number of Son of Employee",
            "Number of Daughter of Employee",
            "Nominee Information",
            "Employee Present Address",
            "Employee Permanent Address",
            "Employee Home District",
            "Employee Nationality",
            "Employee NID Number",
            "Employee Passport Number (If Any)",
            "Employee Driving License Number(If Any)",
            # "Employee Updated Photo",
            # "Employee Scanned Signature"
            # "Phone",
            # "Email",
            # "Gender",
            # "Marital Status",
            # "Emergency Contact Name",
            # "Emergency Contact Relation",
            # "Number Of Son",
            # "Number Of Daughter",
            # "Nominee Name",
            # "Nominee Relation",
            # "Department",
            # "Job Position",
            # "Section",
            # "Unit",
            # "Employee Grade",
            # "Employee Category",
            # "Reporting Manager",
            # #"Company",
            # "Location",
            # "Date joining",
            # #"Contract End Date",
            # "Basic Salary",
            # "Salary Hour",
        ]
    )
    error_data = {
        "Employee ID": [],
        "First Name": [],
        "Last Name": [],
        "Phone": [],
        "Email": [],
        "Gender": [],
        "Department": [],
        "Job Position": [],
        "Unit": [],
        "Employee Grade": [],
        "Employee Category": [],
        "Reporting Manager": [],
        #"Company": [],
        "Location": [],
        "Date joining": [],
        #"Contract End Date": [],
        "Basic Salary": [],
        "Salary Hour": [],
        "Email Error": [],
        "First Name error": [],
        "Name and Email Error": [],
        "Phone error": [],
        "Joining Date Error": [],
        "Last Promotion Date Error": [],
        #"Contract Error": [],
        "Employee ID Error": [],
        "Basic Salary Error": [],
        "Salary Hour Error": [],
        "User ID Error": [],
    }

    # Export the DataFrame to an Excel file
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="work_info_template.xlsx"'
    data_frame.to_excel(response, index=False, engine='xlsxwriter')
    create_work_info = False
    if request.POST.get("create_work_info") == "true":
        create_work_info = True

    if request.method == "POST" and request.FILES.get("file") is not None:
        total_count = 0
        error_lists = []
        success_lists = []
        error_occured = False
        file = request.FILES["file"]
        file_extension = file.name.split(".")[-1].lower()
        data_frame = (
            pd.read_csv(file) if file_extension == "csv" else pd.read_excel(file)
        )
        work_info_dicts = data_frame.to_dict("records")
        existing_badge_ids = set(Employee.objects.values_list("badge_id", flat=True))
        existing_usernames = set(User.objects.values_list("username", flat=True))
        existing_name_emails = set(
            Employee.objects.values_list(
                "employee_first_name", "employee_last_name", "email"
            )
        )
        users = []
        for work_info in work_info_dicts:
            error = False
            #try:
            email = work_info["Employee Email(Personal)"]
            phone = work_info["Employee Contact Number (Personal)"]
            first_name = convert_nan("First Name", work_info)
            last_name = convert_nan("Last Name", work_info)
            badge_id = work_info["Employee ID"] 
            date_joining = work_info["Date Of Joining"]
            # iso_date = datetime.strptime(str(date_joining), "%Y-%m-%d %H:%M:%S")
            # date_of_joining = iso_date.date().isoformat()
            #last_promotion_date = work_info["Last Promotion Date"]
            #contract_end_date = work_info["Contract End Date"]
            # basic_salary = convert_nan("Basic Salary", work_info)
            # salary_hour = convert_nan("Salary Hour", work_info)
            pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

            try:
                if pd.isna(email) or not re.match(pattern, email):
                    work_info["Email Error"] = f"Invalid Email address"
                    #error = True
            except:
                error = True
                work_info["Email Error"] = f"Invalid Email address"

            # try:
            #     pd.to_numeric(basic_salary)
            # except ValueError:
            #     print("salary")
            #     work_info["Basic Salary Error"] = f"Basic Salary must be a number"
            #     error = True

            # try:
            #     pd.to_numeric(salary_hour)
            # except ValueError:
            #     print("hour")
            #     work_info["Salary Hour Error"] = f"Salary Hour must be a number"
            #     error = True

            if pd.isna(first_name):
                work_info["First Name error"] = f"First Name can't be empty"
                error = True

            if pd.isna(phone):
                work_info["Phone error"] = f"Phone Number can't be empty"
                error = True

            name_email_tuple = (first_name, last_name, email)
            if name_email_tuple in existing_name_emails:
                work_info["Name and Email Error"] = (
                    "An employee with this first name, last name, and email already exists."
                )
                error = True
            else:
                existing_name_emails.add(name_email_tuple)

           
            # if badge_id in existing_badge_ids:
            #     work_info["Badge ID Error"] = (
            #         f"An Employee with the badge ID already exists"
            #     )
            #     error = True
            # else:
            #     existing_badge_ids.add(badge_id)

            # if email in existing_usernames:
            #     print('aschi')
            #     work_info["User ID Error"] = (
            #         f"User with the email ID already exists"
            #     )
            #     error = True
            # else:
            #     existing_usernames.add(email)
            if error:
                error_lists.append(work_info)
            else:
                success_lists.append(work_info)

            #except Exception as e:
            # print("Error Occured")
            # error_occured = True
            # logger.error(e)
            if create_work_info or not error_lists:
                # try:

                #     if name_email_tuple in existing_name_emails:

                #         raise ValueError("Invalid input!")

                    # work_info["Name and Email Error"] = (
                    #     "An employee with this first name, last name, and email already exists."
                    # )
                # with transaction.atomic():
                #      bulk_create_user_import(success_lists)
                #      employees = bulk_create_employee_import(success_lists)

                users = bulk_create_user_import(success_lists)
                employees = bulk_create_employee_import(success_lists)
                print(employees, 'emp')
                #sleep(0.5)
                # employee_emails = [row["Employee Email(Personal)"].strip().lower() for row in success_lists]
                # employees = list(Employee.objects.filter(email__in=employee_emails))

                total_count = len(employees)
                if employees:
                    # thread = threading.Thread(
                    # target=set_initial_password, args=(employees,)
                    # )
                    # thread.start()
                    department =  bulk_create_department_import(success_lists)
                    job_position = bulk_create_job_position_import(success_lists)
                    #bulk_create_job_section_import(success_lists)
                    #bulk_create_job_unit_import(success_lists)
                    #bulk_create_job_role_import(success_lists)
                    work_type = bulk_create_work_types(success_lists)
                    #bulk_create_shifts(success_lists)
                    employee_types = bulk_create_employee_types(success_lists)
                    work_data = bulk_create_work_info_import(success_lists)
                    job_experience = bulk_create_job_experience_info_import(success_lists)
                    education = bulk_create_educational_info_import(success_lists)
                    training = bulk_create_professional_training_import(success_lists)
                    reference = bulk_create_job_reference_import(success_lists)

                   
                # except Exception as e:
                #     error_occured = True
                #     logger.error(e)
        error_occured = False
        if error_occured:
            messages.error(request, "something went wrong....")
            data_frame = pd.DataFrame(
                ["The provided titles don't match the default titles."],
                columns=["Title Error"],
            )

            error_count = len(error_lists)
            # Create an HTTP response object with the Excel file
            response = HttpResponse(content_type="application/ms-excel")
            response["Content-Disposition"] = 'attachment; filename="ImportError.xlsx"'
            data_frame.to_excel(response, index=False)
            response["X-Error-Count"] = error_count
            return response
        if error_lists:
            for item in error_lists:
                for key, value in error_data.items():
                    if key in item:
                        value.append(item[key])
                    else:
                        value.append(None)

            keys_to_remove = [
                key
                for key, value in error_data.items()
                if all(v is None for v in value)
            ]

            for key in keys_to_remove:
                del error_data[key]
            data_frame = pd.DataFrame(error_data, columns=error_data.keys())
            error_count = len(error_lists)
            # Create an HTTP response object with the Excel file
            response = HttpResponse(content_type="application/ms-excel")
            response["Content-Disposition"] = 'attachment; filename="ImportError.xlsx"'
            data_frame.to_excel(response, index=False)
            response["X-Error-Count"] = error_count
            return response
        return JsonResponse(
            {
                "Success": "Employees Imported Succefully",
                "success_count": total_count,
            }
        )

    return response


@login_required
@manager_can_enter("employee.view_employee")
def work_info_export(request):
    """
    This method is used to export employee data to xlsx
    """
    if request.META.get("HTTP_HX_REQUEST"):
        context = {
            "export_filter": EmployeeFilter(),
            "export_form": EmployeeExportExcelForm(),
        }
        return render(request, "employee_export_filter.html", context)
    
    employees_data = {}
    selected_columns = []
    form = EmployeeExportExcelForm()
    employees = EmployeeFilter(request.GET).qs
    employees = filtersubordinatesemployeemodel(
        request, employees, "employee.view_employee"
    )
    selected_fields = request.GET.getlist("selected_fields")
    if not selected_fields:
        selected_fields = form.fields["selected_fields"].initial
        ids = request.GET.get("ids")
        id_list = json.loads(ids)
        employees = Employee.objects.filter(id__in=id_list)
    for field in excel_columns:
        value = field[0]
        key = field[1]
        if value in selected_fields:
            selected_columns.append((value, key))
    for column_value, column_name in selected_columns:
        nested_attributes = column_value.split("__")
        employees_data[column_name] = []
        for employee in employees:
            value = employee
            for attr in nested_attributes:
                value = getattr(value, attr, None)
                if value is None:
                    break
            data = str(value) if value is not None else ""

            if type(value) == date:
                user = request.user
                emp = user.employee_get

                # Taking the company_name of the user
                info = EmployeeWorkInformation.objects.filter(employee_id=emp)
                if info.exists():
                    for i in info:
                        employee_company = i.company_id
                    company_name = Company.objects.filter(company=employee_company)
                    emp_company = company_name.first()

                    # Access the date_format attribute directly
                    date_format = (
                        emp_company.date_format if emp_company else "MMM. D, YYYY"
                    )
                else:
                    date_format = "MMM. D, YYYY"
                # Convert the string to a datetime.date object
                start_date = datetime.strptime(str(value), "%Y-%m-%d").date()

                # Print the formatted date for each format
                for format_name, format_string in aiz_DATE_FORMATS.items():
                    if format_name == date_format:
                        data = start_date.strftime(format_string)

            if data == "True":
                data = _("Yes")
            elif data == "False":
                data = _("No")
            job_experiences = EmployeeJobExperiences.objects.filter(employee_id=employee.id)
            
            if column_value == 'employee_job_experience_1':
                company = job_experiences[0].company_name if len(job_experiences)>0 else ""
                designation = job_experiences[0].designation if len(job_experiences)>0 else ""
                experience = job_experiences[0].year_of_experience if len(job_experiences)>0 else ""
                data = company + "," + designation + "," + str(experience)
            elif column_value == 'employee_job_experience_2':
                company = job_experiences[1].company_name if len(job_experiences)>1 else ""
                designation = job_experiences[1].designation if len(job_experiences)>1 else ""
                experience = job_experiences[1].year_of_experience if len(job_experiences)>1 else ""
                data = company + "," + designation + "," + str(experience) 
            elif column_value == 'employee_job_experience_3':
                company = job_experiences[2].company_name if len(job_experiences)>2 else ""
                designation = job_experiences[2].designation if len(job_experiences)>2 else ""
                experience = job_experiences[2].year_of_experience if len(job_experiences)>2 else ""
                data = company + "," + designation + "," + str(experience) 
            elif column_value == 'employee_job_experience_4':
                company = job_experiences[3].company_name if len(job_experiences)>3 else ""
                designation = job_experiences[3].designation if len(job_experiences)>3 else ""
                experience = job_experiences[3].year_of_experience if len(job_experiences)>3 else ""
                data = company + "," + designation + "," + str(experience) 
            
            educations = EmployeeEducation.objects.filter(employee_id=employee.id)
            if column_value == "employee_graduation_subject":
                for i in educations:
                    if i.education_label == "bachelor" or i.education_label == "honours":
                        data = i.subject
                        break
            elif column_value == "employee_graduation_university":
                for i in educations:
                    if i.education_label == "bachelor" or i.education_label == "honours":
                        data =  i.institution_name
                        break
            elif column_value == "employee_post_graduation_subject":
                for i in educations:
                    if i.education_label == "masters" or i.education_label == "kamil":
                        data = i.subject
                        post_graduation_university = i.institution_name
                        break
            elif column_value == "employee_post_graduation_university":
                for i in educations:
                    if i.education_label == "masters" or i.education_label == "kamil":
                        data = i.institution_name
                        break
            elif column_value =="employee_highest_educational_degree":
                data = educations[len(educations)-1].education_label if len(educations)>0 else ""

            if column_value == "employee_training":
                training = EmployeeTraining.objects.filter(employee_id=employee.id)
                data = training[len(training)-1].training_name + "," + training[len(training)-1].institution if len(training)>0 else ""
            
            if column_value == "employee_job_reference":
                references = JobReference.objects.filter(employee_id=employee.id)
                data = references[len(references)-1].reference_name + "," + references[len(references)-1].department +"," + references[len(references)-1].company_name + "," +references[len(references)-1].mobile_number if len(references)>0 else ""
                
            if column_value  == "employee_phone":
                data = employee.phone
            if column_value == "employee_nominee":
                data = employee.employee_nominee_name + "," + employee.employee_nominee_contact + "," + employee.employee_nominee_relation if employee.employee_nominee_name !=None else ""
            
            if column_value == "employee_present_address":
                data = employee.address  if employee.address!= None else "" + "," + employee.zip  if employee.zip != None else "" + "," + employee.city if employee.city != None else "" + "," + employee.state if employee.state != None else "" + "," + employee.country  if employee.country != None else ""


            if column_value == "employee_permanent_address":
                data = employee.employee_permanent_address if employee.employee_permanent_address != None else "" + "," + employee.employee_permanent_address_zip if employee.employee_permanent_address_zip != None else "" + "," + employee.employee_permanent_address_city if employee.employee_permanent_address_city != None else "" + "," + employee.employee_permanent_address_state if employee.employee_permanent_address_state != None else "" + "," + employee.employee_permanent_address_country if employee.employee_permanent_address_country  != None else ""
            
            if column_value == "employee_work_info__casual_id":
                    casual_info = EmployeeWorkInformation.objects.filter(employee_id=employee.id)
                    length = len(casual_info)
                    data = casual_info[length -1].casual_id if length >0 else "N/A"
            if column_value == "employee_casual_joining_date":
                    casual_info = EmployeeWorkInformation.objects.filter(employee_id=employee.id)
                    length = len(casual_info)
                    data = casual_info[length -1].casual_employee_joining_date if length > 0 else "N/A"
            if column_value == "employee_payroll_joining_date":
                    casual_info = EmployeeWorkInformation.objects.filter(employee_id=employee.id)
                    length = len(casual_info)
                    data = casual_info[length -1].casual_employee_payroll_joining_date if length > 0 else "N/A"

            

            if column_value == "employee_photo":
                documents = Document.objects.filter(employee_id=employee.id)
                profile_img = documents.filter(document_category_id__category_title="profile image").first()
                data = profile_img.document.url if profile_img !=None else ""
                
            elif column_value == "employee_signature":
                documents = Document.objects.filter(employee_id=employee.id)
                profile_signature = documents.filter(document_category_id__category_title="profile signature").first()
                data = profile_signature.document.url if profile_signature !=None else ""
                
            employees_data[column_name].append(data)

    data_frame = pd.DataFrame(data=employees_data)
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = 'attachment; filename="employee_export.xlsx"'
    data_frame.to_excel(response, index=False)

    return response


def birthday():
    """
    This method is used to find upcoming birthday and returns the queryset
    """
    today = datetime.now().date()
    last_day_of_month = calendar.monthrange(today.year, today.month)[1]
    employees = Employee.objects.filter(
        is_active=True,
        dob__day__gte=today.day,
        dob__month=today.month,
        dob__day__lte=last_day_of_month,
    ).order_by(F("dob__day").asc(nulls_last=True))

    for employee in employees:
        employee.days_until_birthday = employee.dob.day - today.day
    return employees


@login_required
@enter_if_accessible(feature="birthday_view", perm="employee.view_employee")
def get_employees_birthday(request):
    """
    Render all upcoming birthday employee details for the dashboard.
    """
    employees = birthday()
    default_avatar_url = "https://ui-avatars.com/api/?background=random&name="
    birthdays = [
        {
            "profile": (
                emp.get_avatar()
                if hasattr(emp, "get_avatar")
                else f"{default_avatar_url}{emp.employee_first_name}+{emp.employee_last_name}"
            ),
            "name": f"{emp.employee_first_name} {emp.employee_last_name}",
            "dob": emp.dob.strftime("%d %b %Y"),
            "daysUntilBirthday": (
                _("Today")
                if emp.days_until_birthday == 0
                else (
                    _("Tomorrow")
                    if emp.days_until_birthday == 1
                    else f"In {emp.days_until_birthday} Days"
                )
            ),
            "department": (
                emp.get_department().department if emp.get_department() else ""
            ),
            "job_position": (
                emp.get_job_position().job_position if emp.get_job_position() else ""
            ),
        }
        for emp in employees
    ]
    return render(request, "birthdays_container.html", {"birthdays": birthdays})


@login_required
@manager_can_enter("employee.view_employee")
def dashboard(request):
    """
    This method is used to render individual dashboard for employee module
    """
    upcoming_birthdays = birthday()
    employees = Employee.objects.all()
    employees = filtersubordinates(request, employees, "employee.view_employee")
    active_employees = employees.filter(is_active=True)
    inactive_employees = employees.filter(is_active=False)
    active_ratio = 0
    inactive_ratio = 0
    if employees.exists():
        active_ratio = f"{(len(active_employees) / len(employees)) * 100:.1f}"
        inactive_ratio = f"{(len(inactive_employees) / len(employees)) * 100:.1f}"

    return render(
        request,
        "employee/dashboard/dashboard_employee.html",
        {
            "birthdays": upcoming_birthdays,
            "active_employees": len(active_employees),
            "inactive_employees": len(inactive_employees),
            "total_employees": len(employees),
            "active_ratio": active_ratio,
            "inactive_ratio": inactive_ratio,
        },
    )


@login_required
def total_employees_count(request):
    employees = Employee.objects.all().count()
    return HttpResponse(employees)


@login_required
def joining_today_count(request):
    newbies_today = 0
    if apps.is_installed("recruitment"):
        Candidate = get_aiz_model_class(app_label="recruitment", model="candidate")
        newbies_today = Candidate.objects.filter(
            joining_date__range=[date.today(), date.today() + timedelta(days=1)],
            is_active=True,
        ).count()
    return HttpResponse(newbies_today)


@login_required
def joining_week_count(request):
    newbies_week = 0
    if apps.is_installed("recruitment"):
        Candidate = get_aiz_model_class(app_label="recruitment", model="candidate")
        newbies_week = Candidate.objects.filter(
            joining_date__range=[
                date.today() - timedelta(days=date.today().weekday()),
                date.today() + timedelta(days=6 - date.today().weekday()),
            ],
            is_active=True,
            hired=True,
        ).count()
    return HttpResponse(newbies_week)


@login_required
def dashboard_employee(request):
    """
    Active and in-active employee dashboard
    """
    labels = [
        _("Active"),
        _("In-Active"),
    ]
    employees = Employee.objects.filter()
    response = {
        "dataSet": [
            {
                "label": _("Employees"),
                "data": [
                    len(employees.filter(is_active=True)),
                    len(employees.filter(is_active=False)),
                ],
            },
        ],
        "labels": labels,
    }
    return JsonResponse(response)


@login_required
def dashboard_employee_gender(request):
    """
    This method is used to filter out gender vise employees
    """
    labels = [_("Male"), _("Female"), _("Other")]
    employees = Employee.objects.filter(is_active=True)

    response = {
        "dataSet": [
            {
                "label": _("Employees"),
                "data": [
                    len(employees.filter(gender="male")),
                    len(employees.filter(gender="female")),
                    len(employees.filter(gender="other")),
                ],
            },
        ],
        "labels": labels,
    }
    return JsonResponse(response)


@login_required
def dashboard_employee_relegion(request):
    """
    This method is used to filter out relegion vise employees
    """
    labels = [_("Islam"), _("Hinduism"), _("Buddhism"), _("Christianity")]
    employees = Employee.objects.filter(is_active=True)

    response = {
        "dataSet": [
            {
                "label": _("Employees"),
                "data": [
                    len(employees.filter(employee_religion="islam")),
                    len(employees.filter(employee_religion="hinduism")),
                    len(employees.filter(employee_religion="buddhism")),
                    len(employees.filter(employee_religion="christianity")),
                    
                ],
            },
        ],
        "labels": labels,
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_marital_status(request):
  
    labels = [_("Single"), _("Married"), _("Divorced"),]
    employees = Employee.objects.filter(is_active=True)

    response = {
        "dataSet": [
            {
                "label": _("Employees"),
                "data": [
                    len(employees.filter(marital_status="single")),
                    len(employees.filter(marital_status="married")),
                    len(employees.filter(marital_status="divorced")),
                    
                ],
            },
        ],
        "labels": labels,
    }
    return JsonResponse(response)


@login_required
def dashboard_employee_blood_group(request):
    
    labels = [_("A+"), _("A-"), _("B+"), _("B-"),_("AB+"),_("AB-"),_("O+"),_("O-")]
    employees = Employee.objects.filter(is_active=True)

    response = {
        "dataSet": [
            {
                "label": _("Employees"),
                "data": [
                    len(employees.filter(employee_blood_group="A+")),
                    len(employees.filter(employee_blood_group="A-")),
                    len(employees.filter(employee_blood_group="B+")),
                    len(employees.filter(employee_blood_group="B-")),
                    len(employees.filter(employee_blood_group="AB+")),
                    len(employees.filter(employee_blood_group="AB-")),
                    len(employees.filter(employee_blood_group="O+")),
                    len(employees.filter(employee_blood_group="O-")),
                    
                ],
            },
        ],
        "labels": labels,
    }
    return JsonResponse(response)


@login_required
def dashboard_employee_department(request):
    """
    This method is used to find the count of employees corresponding to the departments
    """
    labels = []
    count = []
    departments = Department.objects.all()
    for dept in departments:
        if len(
            Employee.objects.filter(
                employee_work_info__department_id__department=dept, is_active=True
            )
        ):
            labels.append(dept.department)
            count.append(
                len(
                    Employee.objects.filter(
                        employee_work_info__department_id__department=dept,
                        is_active=True,
                    )
                )
            )
    response = {
        "dataSet": [{"label": "Department", "data": count}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_job_position(request):
    
    labels = []
    count = []
    positions = JobPosition.objects.all()
    for dept in positions:
        if len(
            Employee.objects.filter(
                employee_work_info__job_position_id=dept, is_active=True
            )
        ):
            labels.append(dept.job_position)
            count.append(
                len(
                    Employee.objects.filter(
                        employee_work_info__job_position_id=dept,
                        is_active=True,
                    )
                )
            )
    response = {
        "dataSet": [{"label": "JobPosition", "data": count}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_job_section(request):
    
    labels = []
    count = []
    sections = EmployeeSection.objects.all()
    for dept in sections:
        if len(
            Employee.objects.filter(
                employee_work_info__employee_section_id=dept, is_active=True
            )
        ):
            labels.append(dept.employee_section)
            count.append(
                len(
                    Employee.objects.filter(
                        employee_work_info__employee_section_id=dept,
                        is_active=True,
                    )
                )
            )
    response = {
        "dataSet": [{"label": "EmployeeSection", "data": count}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_job_unit(request):
    
    labels = []
    count = []
    units = EmployeeUnit.objects.all()
    for dept in units:
        if len(
            Employee.objects.filter(
                employee_work_info__employee_unit_id=dept, is_active=True
            )
        ):
            labels.append(dept.employee_unit)
            count.append(
                len(
                    Employee.objects.filter(
                        employee_work_info__employee_unit_id=dept,
                        is_active=True,
                    )
                )
            )
    response = {
        "dataSet": [{"label": "EmployeeUnit", "data": count}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_job_grade(request):
    labels = []
    count = []
    grade = []
    work_info = EmployeeWorkInformation.objects.all()
    for work in work_info:
        grade.append(work.employee_grade)
    grade = set(grade)
    for dept in grade:
        if len(
            Employee.objects.filter(
                employee_work_info__employee_grade=dept, is_active=True
            )
        ):
            labels.append(dept)
            count.append(
                len(
                    Employee.objects.filter(
                        employee_work_info__employee_grade=dept,
                        is_active=True,
                    )
                )
            )
    response = {
        "dataSet": [{"label": "Grade", "data": count}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)


@login_required
def dashboard_employee_category(request):
    labels = []
    count = []
    employee_type = EmployeeType.objects.all()
    for dept in employee_type:
        if len(
            Employee.objects.filter(
                employee_work_info__employee_type_id=dept, is_active=True
            )
        ):
            labels.append(dept.employee_type)
            count.append(
                len(
                    Employee.objects.filter(
                        employee_work_info__employee_type_id=dept,
                        is_active=True,
                    )
                )
            )
    response = {
        "dataSet": [{"label": "Category", "data": count}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_home_town(request):
    labels = []
    count_district= []
    employee = Employee.objects.filter(is_active=True).values("employee_home_district").annotate(total=Count("id"))
    print(employee, 'employee')

    for item in employee:
        print(item, 'item')
        labels.append(item['employee_home_district'])
        count_district.append(item['total'])
    
    
    response = {
        "dataSet": [{"label": "homeTown", "data": count_district}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_graduation_subject(request):
    labels = []
    count_subject= []
    education_lavel = ["bachelor", "honours", "pass", "fazil"]
    education = EmployeeEducation.objects.filter(is_active=True, education_label__in=education_lavel).values("subject").annotate(total=Count("id"))

    for subject in education:
        labels.append(subject['subject'])
        count_subject.append(subject['total'])
    
    
    response = {
        "dataSet": [{"label": "gSubject", "data": count_subject}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_graduation_university(request):
    labels = []
    count_university= []
    education_lavel = ["bachelor", "honours", "pass", "fazil"]
    education = EmployeeEducation.objects.filter(is_active=True, education_label__in=education_lavel).values("institution_name").annotate(total=Count("id"))

    for university in education:
        labels.append(university['institution_name'])
        count_university.append(university['total'])
    
    
    response = {
        "dataSet": [{"label": "gUniversity", "data": count_university}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_post_graduation_subject(request):
    labels = []
    count_subject= []
    education_lavel = ["masters", "kamil", "mphil", "phd"]
    education = EmployeeEducation.objects.filter(is_active=True, education_label__in=education_lavel).values("subject").annotate(total=Count("id"))

    for subject in education:
        labels.append(subject['subject'])
        count_subject.append(subject['total'])
    
    
    response = {
        "dataSet": [{"label": "pgSubject", "data": count_subject}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)

@login_required
def dashboard_employee_post_graduation_university(request):
    labels = []
    count_university= []
    education_lavel = ["masters", "kamil", "mphil", "phd"]
    education = EmployeeEducation.objects.filter(is_active=True, education_label__in=education_lavel).values("institution_name").annotate(total=Count("id"))

    for university in education:
        labels.append(university['institution_name'])
        count_university.append(university['total'])
    
    
    response = {
        "dataSet": [{"label": "pgSubject", "data": count_university}],
        "labels": labels,
        "message": _("No Data Found..."),
    }
    return JsonResponse(response)


@login_required
def widget_filter(request):
    """
    This method is used to return all the ids of the employees
    """
    ids = EmployeeFilter(request.GET).qs.values_list("id", flat=True)
    return JsonResponse({"ids": list(ids)})


@login_required
def employee_select(request):
    """
    This method is used to return all the id of the employees to select the employee row
    """
    page_number = request.GET.get("page")
    employees = Employee.objects.filter()
    if page_number == "all":
        employees = Employee.objects.filter(is_active=True)

    employee_ids = [str(emp.id) for emp in employees]
    total_count = employees.count()

    context = {"employee_ids": employee_ids, "total_count": total_count}

    return JsonResponse(context, safe=False)


@login_required
@manager_can_enter("employee.view_employee")
def employee_select_filter(request):
    """
    This method is used to return all the ids of the filtered employees
    """
    page_number = request.GET.get("page")
    if page_number == "all":
        employee_filter = EmployeeFilter(
            request.GET, queryset=Employee.objects.filter()
        )

        # Get the filtered queryset
        filtered_employees = filtersubordinatesemployeemodel(
            request=request, queryset=employee_filter.qs, perm="employee.view_employee"
        )
        employee_ids = [str(emp.id) for emp in filtered_employees]
        total_count = filtered_employees.count()

        context = {"employee_ids": employee_ids, "total_count": total_count}

        return JsonResponse(context)


@login_required
@hx_request_required
@manager_can_enter(perm="employee.view_employeenote")
def note_tab(request, emp_id):
    """
    This function is used to view note tab of an employee in employee individual
    & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    emp_id (int): The id of the employee.

    Returns: return note-tab template

    """
    employee_obj = Employee.objects.get(id=emp_id)
    notes = EmployeeNote.objects.filter(employee_id=emp_id).order_by("-id")

    return render(
        request,
        "tabs/note_tab.html",
        {"employee": employee_obj, "notes": notes},
    )


@login_required
@hx_request_required
@manager_can_enter(perm="employee.add_employeenote")
def add_note(request, emp_id=None):
    """
    This method renders template component to add candidate remark
    """

    form = EmployeeNoteForm(initial={"employee_id": emp_id})
    if request.method == "POST":
        form = EmployeeNoteForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            note, attachment_ids = form.save(commit=False)
            employee = Employee.objects.get(id=emp_id)
            note.employee_id = employee
            note.updated_by = request.user.employee_get
            note.save()
            note.note_files.set(attachment_ids)
            messages.success(request, _("Note added successfully.."))
            response = render(request, "tabs/add_note.html", {"form": form})
            return redirect(f"/employee/note-tab/{emp_id}")

    employee_obj = Employee.objects.get(id=emp_id)
    return render(
        request,
        "tabs/add_note.html",
        {
            "employee": employee_obj,
            "form": form,
        },
    )


@login_required
@manager_can_enter(perm="employee.change_employeenote")
def employee_note_update(request, note_id):
    """
    This method is used to update the note
    Args:
        id : stage note instance id
    """

    note = EmployeeNote.objects.get(id=note_id)

    form = EmployeeNoteForm(instance=note)
    if request.POST:
        form = EmployeeNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, _("Note updated successfully..."))
            response = render(
                request,
                "tabs/update_note.html",
                {"form": form},
            )
            return HttpResponse(
                response.content.decode("utf-8") + "<script>location.reload();</script>"
            )
    return render(
        request,
        "tabs/update_note.html",
        {
            "form": form,
        },
    )


@login_required
@manager_can_enter(perm="employee.delete_employeenote")
def employee_note_delete(request, note_id):
    """
    This method is used to delete the note
    Args:
        id : stage note instance id
    """

    note = EmployeeNote.objects.get(id=note_id)
    note.delete()
    messages.success(request, _("Note deleted successfully."))
    return HttpResponse()


@login_required
@hx_request_required
@manager_can_enter(perm="employee.add_notefiles")
def add_more_employee_files(request, note_id):
    """
    This method is used to Add more files to the Employee note.
    Args:
        id : stage note instance id
    """
    note = EmployeeNote.objects.get(id=note_id)
    employee_id = note.employee_id.id
    if request.method == "POST":
        files = request.FILES.getlist("files")
        files_ids = []
        for file in files:
            instance = NoteFiles.objects.create(files=file)
            files_ids.append(instance.id)

            note.note_files.add(instance.id)
    return redirect(f"/employee/note-tab/{employee_id}")


@login_required
@hx_request_required
@manager_can_enter(perm="employee.delete_notefiles")
def delete_employee_note_file(request, note_file_id):
    """
    This method is used to delete the stage note file
    Args:
        id : stage file instance id
    """
    file = NoteFiles.objects.get(id=note_file_id)
    file.delete()
    return HttpResponse()


@login_required
@hx_request_required
@owner_can_enter("employee.view_bonuspoint", Employee)
def bonus_points_tab(request, emp_id):
    """
    This function is used to view Bonus Points tab of an employee in employee individual
    & profile view.

    Parameters:
    request (HttpRequest): The HTTP request object.
    emp_id (int): The id of the employee.

    Returns: return bonus_points template

    """
    employee_obj = Employee.objects.get(id=emp_id)
    points = BonusPoint.objects.get(employee_id=emp_id)
    if apps.is_installed("payroll"):
        Reimbursement = get_aiz_model_class(
            app_label="payroll", model="reimbursement"
        )
        requested_bonus_points = Reimbursement.objects.filter(
            employee_id=emp_id, type="bonus_encashment", status="requested"
        )
    else:
        requested_bonus_points = QuerySet().none()
    trackings = points.tracking()
    activity_list = []
    for history in trackings:
        activity_list.append(
            {
                "type": history["type"],
                "date": history["pair"][0].history_date,
                "points": history["pair"][0].points - history["pair"][1].points,
                "user": getattr(
                    User.objects.filter(id=history["pair"][0].history_user_id).first(),
                    "employee_get",
                    None,
                ),
                "reason": history["pair"][0].reason,
            }
        )
    for requested in requested_bonus_points:
        activity_list.append(
            {
                "type": "requested",
                "date": requested.created_at,
                "points": requested.bonus_to_encash,
                "user": employee_obj.employee_user_id,
                "reason": "Redeemed points",
            }
        )
    activity_list = sorted(activity_list, key=lambda x: x["date"], reverse=True)
    context = {
        "employee": employee_obj,
        "points": points,
        "activity_list": activity_list,
    }
    return render(
        request,
        "tabs/bonus_points.html",
        context,
    )


@login_required
@manager_can_enter(perm="employee.add_bonuspoint")
def add_bonus_points(request, emp_id):
    """
    This function is used to add bonus points to an employee

    Args:
        request (HttpRequest): The HTTP request object.
        emp_id (int): The id of the employee.

    Returns: returns add_points form
    """

    bonus_point = BonusPoint.objects.get(employee_id=emp_id)
    form = BonusPointAddForm()
    if request.method == "POST":
        form = BonusPointAddForm(
            request.POST,
            request.FILES,
        )
        if form.is_valid():
            form.save(commit=False)
            bonus_point.points += form.cleaned_data["points"]
            bonus_point.reason = form.cleaned_data["reason"]
            bonus_point.save()
            messages.success(
                request,
                _("Added {} points to the bonus account").format(
                    form.cleaned_data["points"]
                ),
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

    return render(
        request,
        "tabs/forms/add_points.html",
        {
            "form": form,
            "emp_id": emp_id,
        },
    )


@login_required
@owner_can_enter("employee.view_bonuspoint", Employee)
def redeem_points(request, emp_id):
    """
    This function is used to redeem bonus points for an employee

    Args:
        request (HttpRequest): The HTTP request object.
        emp_id (int): The id of the employee.

    Returns: returns redeem_points_form form
    """
    employee = Employee.objects.get(id=emp_id)
    avialable_points = 0
    if BonusPoint.objects.filter(employee_id=employee).exists():
        avialable_points = (
            BonusPoint.objects.filter(employee_id=employee).first().points
        )
    form = BonusPointRedeemForm(initial={"points": avialable_points})
    form.instance.employee_id = employee

    amount_for_bonus_point = 0
    if apps.is_installed("payroll"):
        EncashmentGeneralSettings = get_aiz_model_class(
            app_label="payroll", model="encashmentgeneralsettings"
        )
        amount_for_bonus_point = (
            EncashmentGeneralSettings.objects.first().bonus_amount
            if EncashmentGeneralSettings.objects.first()
            else 1
        )
    if request.method == "POST":
        form = BonusPointRedeemForm(request.POST)
        form.instance.employee_id = employee
        if form.is_valid():
            form.save(commit=False)
            points = form.cleaned_data["points"]
            amount = amount_for_bonus_point * points
            if apps.is_installed("payroll"):
                Reimbursement = get_aiz_model_class(
                    app_label="payroll", model="reimbursement"
                )
                Reimbursement.objects.create(
                    title=f"Bonus point Redeem for {employee}",
                    type="bonus_encashment",
                    employee_id=employee,
                    bonus_to_encash=points,
                    amount=amount,
                    description=f"{employee} want to redeem {points} points",
                    allowance_on=date.today(),
                )
            return HttpResponse("<script>window.location.reload();</script>")
    return render(
        request,
        "tabs/forms/redeem_points_form.html",
        {
            "form": form,
            "employee": employee,
        },
    )


@login_required
def organisation_chart(request):
    """
    This method is used to view oganisation chart
    """
    selected_company = request.session.get("selected_company")
    if (
        request.GET.get("employee_work_info__company_id") == None
        and selected_company != "all"
    ):
        reporting_managers = Employee.objects.filter(
            reporting_manager__isnull=False,
            employee_work_info__company_id=selected_company,
        ).distinct()
    else:
        reporting_managers = Employee.objects.filter(
            reporting_manager__isnull=False
        ).distinct()

    # Iterate through the queryset and add reporting manager id and name to the dictionary
    result_dict = {item.id: item.get_full_name() for item in reporting_managers}

    entered_req_managers = []

    # Helper function to recursively create the hierarchy structure
    def create_hierarchy(manager):
        """
        Hierarchy generator method
        """
        nodes = []
        # check the manager is a reporting manager if yes, store it into entered_req_managers
        if manager.id in result_dict.keys():
            entered_req_managers.append(manager)
        # filter the subordinates
        subordinates = Employee.objects.filter(
            employee_work_info__reporting_manager_id=manager
        ).exclude(id=manager.id)

        # itrating through subordinates
        for employee in subordinates:
            if employee in entered_req_managers:
                continue
            # check the employee is a reporting manager if yes,remove className store
            # it into entered_req_managers
            if employee.id in result_dict.keys():
                nodes.append(
                    {
                        "name": employee.get_full_name(),
                        "title": getattr(
                            employee.get_job_position(), "job_position", _("Not set")
                        ),
                        "children": create_hierarchy(employee),
                    }
                )
                entered_req_managers.append(employee)

            else:
                nodes.append(
                    {
                        "name": employee.get_full_name(),
                        "title": getattr(
                            employee.get_job_position(), "job_position", _("Not set")
                        ),
                        "className": "middle-level",
                        "children": create_hierarchy(employee),
                    }
                )
        return nodes

    selected_company = request.session.get("selected_company")
    if (
        request.GET.get("employee_work_info__company_id") == None
        and selected_company != "all"
    ):
        reporting_managers = Employee.objects.filter(
            reporting_manager__isnull=False,
            employee_work_info__company_id=selected_company,
        ).distinct()
    else:
        reporting_managers = Employee.objects.filter(
            reporting_manager__isnull=False
        ).distinct()

    manager = request.user.employee_get

    if len(reporting_managers) == 0:
        new_dict = {}
    else:
        new_dict = {reporting_managers[0].id: _("My view"), **result_dict}
    # POST method is used to change the reporting manager
    if request.method == "POST":
        if request.POST.get("manager_id"):
            manager_id = int(request.POST.get("manager_id"))
            manager = Employee.objects.get(id=manager_id)
        node = {
            "name": manager.get_full_name(),
            "title": getattr(manager.get_job_position(), "job_position", _("Not set")),
            "children": create_hierarchy(manager),
        }
        context = {"act_datasource": node}
        return render(request, "organisation_chart/chart.html", context=context)

    node = {
        "name": manager.get_full_name(),
        "title": getattr(manager.get_job_position(), "job_position", _("Not set")),
        "children": create_hierarchy(manager),
    }

    context = {
        "act_datasource": node,
        "reporting_manager_dict": new_dict,
        "act_manager_id": manager.id,
    }
    return render(request, "organisation_chart/org_chart.html", context=context)


@login_required
@permission_required("payroll.add_encashmentgeneralsettings")
def encashment_condition_create(request):
    """
    Handle the creation and updating of encashment general settings.
    """
    if apps.is_installed("payroll"):
        from payroll.forms.forms import EncashmentGeneralSettingsForm

        EncashmentGeneralSettings = get_aiz_model_class(
            app_label="payroll", model="encashmentgeneralsettings"
        )
        instance = (
            EncashmentGeneralSettings.objects.first()
            if apps.is_installed("payroll")
            else QuerySet().none()
        )

        if request.method == "POST":
            encashment_form = EncashmentGeneralSettingsForm(
                request.POST, instance=instance
            )
            if encashment_form.is_valid():
                encashment_form.save()
                messages.success(request, _("Settings updated."))
                return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        else:
            encashment_form = EncashmentGeneralSettingsForm(instance=instance)

        return render(
            request,
            "settings/encashment_settings.html",
            {"encashment_form": encashment_form},
        )

    messages.warning(request, _("Payroll app not installed"))
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@permission_required("employee.add_employeegeneralsetting")
def initial_prefix(request):
    """
    This method is used to set the initial prefix using a form.
    """
    instance = EmployeeGeneralSetting.objects.first()  # Get the first instance or None
    if not instance:
        instance = EmployeeGeneralSetting()  # Create a new instance if none exists

    if request.method == "POST":
        form = EmployeeGeneralSettingPrefixForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Initial prefix updated successfully.")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        else:
            messages.error(request, "There was an error updating the prefix.")
    else:
        form = EmployeeGeneralSettingPrefixForm(instance=instance)

    return render(request, "settings/settings.html", {"prefix_form": form})


@login_required
@manager_can_enter("employee.view_employee")
def first_last_badge(request):
    """
    This method is used to return the first last badge ids in grouped and ordere
    """
    badge_ids = get_ordered_badge_ids()

    return render(
        request,
        "employee_personal_info/first_last_badge.html",
        {"badge_ids": badge_ids},
    )


@login_required
@hx_request_required
@manager_can_enter("employee.view_employee")
def employee_get_mail_log(request):
    """
    This method is used to track mails sent along with the status
    """
    employee_id = request.GET["emp_id"]
    employee = Employee.objects.get(id=employee_id)
    tracked_mails = EmailLog.objects.filter(to__icontains=employee.email)
    if employee.employee_work_info and employee.employee_work_info.email:
        tracked_mails = tracked_mails | EmailLog.objects.filter(
            to__icontains=employee.employee_work_info.email
        )
    tracked_mails = tracked_mails.order_by("-created_at")

    return render(request, "tabs/mail_log.html", {"tracked_mails": tracked_mails})


@login_required
def get_job_positions(request):
    department_id = request.GET.get("department_id")
    job_positions = (
        JobPosition.objects.filter(department_id=department_id).values_list(
            "id", "job_position"
        )
        if department_id
        else []
    )

    return JsonResponse({"job_positions": dict(job_positions)})


@login_required
def get_document_category(request):
    document_category = (
        DocumentCategory.objects.all().values_list(
            "id", "category_title"
        )
    )

    return JsonResponse({"document_category": dict(document_category)})



@login_required
def get_employee_section(request):
    department_id = request.GET.get("department_id")
    employee_sections = (
        EmployeeSection.objects.filter(department_id=department_id).values_list(
            "id", "employee_section"
        )
        if department_id
        else []
    )
    return JsonResponse({"employee_sections": dict(employee_sections)})


@login_required
def get_job_roles(request):
    """
    Retrieve job roles associated with a specific Job Position.

    This view function extracts the job_id from the GET request, queries the
    JobRole model for job roles that match the provided job_position_id, and
    returns the results as a JSON response.
    """
    job_id = request.GET.get("job_id")
    job_roles = JobRole.objects.filter(job_position_id=job_id).values_list(
        "id", "job_role"
    )
    return JsonResponse({"job_roles": dict(job_roles)})

@login_required
def get_employee_unit(request):
    job_id = request.GET.get("job_id")
    employee_units = EmployeeUnit.objects.filter(employee_section_id=job_id).values_list(
        "id", "employee_unit"
    )
    return JsonResponse({"employee_units": dict(employee_units)})


@login_required
@permission_required("employee.view_employeetag")
def employee_tag_view(request):
    """
    This method is used to Employee tags
    """
    employeetags = EmployeeTag.objects.all()
    return render(
        request,
        "base/tags/employee_tags.html",
        {"employeetags": employeetags},
    )


@login_required
@hx_request_required
@permission_required("employee.add_employeetag")
def employee_tag_create(request):
    """
    This method renders form and template to create Ticket type
    """
    form = EmployeeTagForm()
    if request.method == "POST":
        form = EmployeeTagForm(request.POST)
        if form.is_valid():
            form.save()
            form = EmployeeTagForm()
            messages.success(request, _("Tag has been created successfully!"))
    return render(
        request,
        "base/employee_tag/employee_tag_form.html",
        {
            "form": form,
        },
    )


@login_required
@hx_request_required
@permission_required("employee.add_employeetag")
def employee_tag_update(request, tag_id):
    """
    This method renders form and template to create Ticket type
    """
    tag = EmployeeTag.objects.get(id=tag_id)
    form = EmployeeTagForm(instance=tag)
    if request.method == "POST":
        form = EmployeeTagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            form = EmployeeTagForm()
            messages.success(request, _("Tag has been updated successfully!"))
            return HttpResponse("<script>window.location.reload()</script>")
    return render(
        request,
        "base/employee_tag/employee_tag_form.html",
        {"form": form, "tag_id": tag_id},
    )
