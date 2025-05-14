"""
employee/methods.py
"""

import logging
import threading
from datetime import datetime
from itertools import groupby

import pandas as pd
from django.apps import apps
from django.contrib.auth.models import User
from django.db import models
from datetime import date


from base.context_processors import get_initial_prefix
from base.models import (
    Company,
    Department,
    EmployeeShift,
    EmployeeType,
    JobPosition,
    JobRole,
    WorkType,
    EmployeeSection,
    EmployeeUnit,
)
from employee.models import Employee, EmployeeWorkInformation

logger = logging.getLogger(__name__)


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


def dynamic_prefix_sort(item):
    """
    Sorts items based on a dynamic prefix length.
    """
    # Assuming the dynamic prefix length is 3
    prefix = get_initial_prefix(None)["get_initial_prefix"]

    prefix_length = len(prefix) if len(prefix) >= 3 else 3
    return item[:prefix_length]


def get_ordered_badge_ids():
    """
    This method is used to return ordered badge ids
    """
    employees = Employee.objects.all()
    data = (
        employees.exclude(badge_id=None)
        .order_by("badge_id")
        .values_list("badge_id", flat=True)
    )
    if not data.first():
        data = [
            f'{get_initial_prefix(None)["get_initial_prefix"]}0001',
        ]
    # Separate pure number strings and convert them to integers
    pure_numbers = [int(item) for item in data if item.isdigit()]

    # Remove pure number strings from the original data
    data = [item for item in data if not item.isdigit()]

    # Sort the remaining data by dynamic prefixes
    sorted_data = sorted(data, key=dynamic_prefix_sort)

    # Group the sorted data by dynamic prefixes
    grouped_data = [
        list(group) for _, group in groupby(sorted_data, key=dynamic_prefix_sort)
    ]

    # Sort each subgroup alphabetically and numerically
    for group in grouped_data:
        group.sort()
        filtered_group = [
            item for item in group if any(char.isdigit() for char in item)
        ]
        filtered_group.sort(key=lambda x: int("".join(filter(str.isdigit, x))))

    # Create a list containing the first and last items from each group
    result = [[group[0], group[-1]] for group in grouped_data]

    # Add the list of pure numbers at the beginning
    if pure_numbers:
        result.insert(0, [pure_numbers[0], pure_numbers[-1]])
    return result


def check_relationship_with_employee_model(model):
    """
    Checks the relationship of a given model with the Employee model.

    This function iterates through all the fields of the specified model
    and identifies fields that are either `ForeignKey` or `ManyToManyField`
    and are related to the `Employee` model. For each such field, it adds
    the field name and the type of relationship to a list.
    """
    related_fields = []
    for field in model._meta.get_fields():
        # Check if the field is a ForeignKey or ManyToManyField and related to Employee
        if isinstance(field, models.ForeignKey) and field.related_model == Employee:
            related_fields.append((field.name, "ForeignKey"))
        elif (
            isinstance(field, models.ManyToManyField)
            and field.related_model == Employee
        ):
            related_fields.append((field.name, "ManyToManyField"))
    return related_fields


def bulk_create_user_import(success_lists):
    """
    Bulk creation of user instances based on the excel import of employees
    """
    user_obj_list = []
    cleaned_success_list = [
    {k.strip(): v for k, v in row.items()} for row in success_lists
]
    existing_usernames = {
        user.username
        for user in User.objects.filter(
            username__in=[row["Employee Email(Personal)"] for row in cleaned_success_list]
        )
    }

    for work_info in success_lists:
        email = work_info["Employee Email(Personal)"]
        if email in existing_usernames:
            continue

        phone = work_info["Employee Contact Number (Personal)"]
        user_obj = User(
            username=email,
            email=email,
            password=str(phone).strip(),
            is_superuser=False,
        )
        user_obj_list.append(user_obj)
    result = []
    if user_obj_list:
        result = User.objects.bulk_create(user_obj_list)
    return result


def bulk_create_employee_import(success_lists):
    """
    Bulk creation of employee instances based on the excel import of employees
    """
    employee_obj_list = []
    existing_users = {
        user.username: user
        for user in User.objects.filter(
            username__in=[row["Employee Email(Personal)"] for row in success_lists]
        )
    }

    for work_info in success_lists:
        email = work_info["Employee Email(Personal)"]
        user = existing_users.get(email)
        if not user:
            continue

        badge_id = work_info["Employee ID"]
        first_name = convert_nan("First Name", work_info)
        last_name = convert_nan("Last Name", work_info)
        phone = work_info["Employee Contact Number (Personal)"]
        gender = work_info.get("Employee Gender", "").lower()
        address = work_info["Employee Present Address"]
        #address1, zip, city,state,country = [part.strip() for part in address.split(',')]
        permanent_address = work_info["Employee Permanent Address"]
        dob = work_info["Date of Birth"] if work_info["Date of Birth"] !="" else date.today()
        dt = datetime.strptime(str(dob), "%Y-%m-%d %H:%M:%S")
        date_str = dt.date().isoformat()  # This gives '2000-05-05'

        marital_status = work_info["Employee Marital Status"]
        emergency_contact = work_info["Emergency Contact Number"]
        blood_group = work_info["Employee Blood Group"]
        religion=work_info["Employee Religion"]
        nationality=work_info["Employee Nationality"]
        nid = work_info["Employee NID Number"]
        passport_number = work_info["Employee Passport Number(If Any)"]
        driving_license = work_info["Employee Driving License Number(If Any)"]
        home_district = work_info["Employee Home District"]
        father_name=work_info["Employee Father's Name (According to NID)"]
        mother_name = work_info["Employee Mother's Name (According to NID)"]
        spouse_name= work_info["Employee Spouse Name (According to NID)_If Married"]
        number_of_son = work_info["Number of Son of Employee"]
        number_of_daughter = work_info["Number of Daughter of Employee"]
        nominee = work_info["Nominee Information"]
        n_name,n_number,n_relation = [part.strip() for part in nominee.split(',')]
        employee_obj = Employee(
            employee_user_id=user,
            badge_id=badge_id,
            employee_first_name=first_name,
            employee_last_name=last_name,
            email=email,
            phone=phone,
            gender=gender,
            address=address,
            employee_permanent_address=permanent_address,
            dob=date_str,
            marital_status=marital_status,
            emergency_contact=emergency_contact,
            employee_blood_group=blood_group,
            employee_religion=religion,
            employee_nationality=nationality,
            employee_nid_number=nid,
            employee_passport_number=passport_number,
            employee_driving_license_number=driving_license,
            employee_home_district=home_district,
            employee_father_name=father_name,
            employee_mother_name=mother_name,
            employee_spouse_name=spouse_name,
            employee_number_of_son=number_of_son,
            employee_number_of_daughter=number_of_daughter,
            employee_nominee_name=n_name,
            employee_nominee_contact=n_number,
            employee_nominee_relation=n_relation
        )
        employee_obj_list.append(employee_obj)
    result = []
    if employee_obj_list:
        result = Employee.objects.bulk_create(employee_obj_list)

    return result


def set_initial_password(employees):
    """
    method to set initial password
    """

    logger.info("started to set initial password")
    for employee in employees:
        try:
            employee.employee_user_id.set_password(str(employee.phone))
            employee.employee_user_id.save()
        except Exception as e:
            logger.error(f"falied to set initial password for {employee}")
    logger.info("initial password configured")


def optimize_reporting_manager_lookup(success_lists):
    """
    Optimizes the lookup of reporting managers from a list of work information.

    This function identifies unique reporting manager names from the provided
    list of work information, queries all matching `Employee` objects in a
    single database query, and creates a dictionary for quick lookups based
    on the full name of the reporting managers.
    """
    # Step 1: Collect unique reporting manager names
    unique_managers = set()
    for work_info in success_lists:
        reporting_manager = convert_nan("Reporting Manager", work_info)
        if isinstance(reporting_manager, str) and " " in reporting_manager:
            unique_managers.add(reporting_manager)

    # Step 2: Query all relevant Employee objects in one go
    manager_names = list(unique_managers)
    employees = Employee.objects.filter(
        employee_first_name__in=[name.split(" ")[0] for name in manager_names],
        employee_last_name__in=[name.split(" ")[1] for name in manager_names],
    )

    print(manager_names, 'manger_namew')

    # Step 3: Create a dictionary for quick lookups
    employee_dict = {
        f"{employee.employee_first_name} {employee.employee_last_name}": employee
        for employee in employees
    }
    return employee_dict


def bulk_create_department_import(success_lists):
    """
    Bulk creation of department instances based on the excel import of employees
    """
    departments_to_import = {
        convert_nan("Department", work_info) for work_info in success_lists
    }
    existing_departments = {dep.department for dep in Department.objects.all()}
    department_obj_list = []

    for department in departments_to_import:
        if department and department not in existing_departments:
            department_obj = Department(department=department)
            department_obj_list.append(department_obj)
            existing_departments.add(department)

    if department_obj_list:
        Department.objects.bulk_create(department_obj_list)


def bulk_create_job_position_import(success_lists):
    """
    Bulk creation of Job Position instances based on the excel import of employees
    """
    job_positions_to_import = {
        (convert_nan("Job Position", work_info), convert_nan("Department", work_info))
        for work_info in success_lists
    }
    departments = {dep.department: dep for dep in Department.objects.all()}
    existing_job_positions = {
        (job_position.job_position, job_position.department_id): job_position
        for job_position in JobPosition.objects.all()
    }
    job_position_obj_list = []
    for job_position, department_name in job_positions_to_import:
        if not job_position or not department_name:
            continue

        department_obj = departments.get(department_name)
        if not department_obj:
            continue

        # Check if this Job Position already exists for this department
        if (job_position, department_obj.id) not in existing_job_positions:
            job_position_obj = JobPosition(
                department_id=department_obj, job_position=job_position
            )
            job_position_obj_list.append(job_position_obj)
            existing_job_positions[(job_position, department_obj.id)] = job_position_obj

    if job_position_obj_list:
        JobPosition.objects.bulk_create(job_position_obj_list)

# def bulk_create_job_section_import(success_lists):
#     """
#     Bulk creation of Job Section instances based on the excel import of employees
#     """
#     job_section_to_import = {
#         (convert_nan("Employee Section", work_info), convert_nan("Department", work_info))
#         for work_info in success_lists
#     }
#     departments = {dep.department: dep for dep in Department.objects.all()}
#     existing_job_section = {
#         (job_section.employee_section, job_section.department_id): job_section
#         for job_section in EmployeeSection.objects.all()
#     }
#     job_section_obj_list = []
#     for job_section, department_name in job_section_to_import:
#         if not job_section or not department_name:
#             continue

#         department_obj = departments.get(department_name)
#         if not department_obj:
#             continue

#         # Check if this Job Position already exists for this department
#         if (job_section, department_obj.id) not in existing_job_section:
#             job_section_obj = EmployeeSection(
#                 department_id=department_obj, employee_section=job_section
#             )
#             job_section_obj_list.append(job_section_obj)
#             existing_job_section[(job_section, department_obj.id)] = job_section_obj

#     if job_section_obj_list:
#         EmployeeSection.objects.bulk_create(job_section_obj_list)

def bulk_create_job_unit_import(success_lists):
    """
    Bulk creation of Job unit instances based on the excel import of employees
    """
    job_unit_to_import = {
        (convert_nan("Employee Unit", work_info), convert_nan("Employee Section", work_info))
        for work_info in success_lists
    }
    sections = {dep.employee_section: dep for dep in EmployeeSection.objects.all()}
    existing_job_unit = {
        (job_unit.employee_unit, job_unit.employee_section_id): job_unit
        for job_unit in EmployeeUnit.objects.all()
    }

    job_unit_obj_list = []
    for job_unit, employee_section in job_unit_to_import:
        if not job_unit or not employee_section:
            continue

        section_obj = sections.get(employee_section)
        if not section_obj:
            continue

        # Check if this Job Position already exists for this department
        if (job_unit, section_obj.id) not in existing_job_unit:
            job_unit_obj = EmployeeUnit(
                employee_section_id=section_obj, employee_unit=job_unit
            )
            job_unit_obj_list.append(job_unit_obj)
            existing_job_unit[(job_unit, section_obj.id)] = job_unit_obj

    if job_unit_obj_list:
        EmployeeSection.objects.bulk_create(job_unit_obj_list)


def bulk_create_job_role_import(success_lists):
    """
    Bulk creation of job role instances based on the excel import of employees
    """
    # Collect job role names and their associated Job Positions into a set as tubles
    job_roles_to_import = {
        (convert_nan("Job Role", work_info), convert_nan("Job Position", work_info))
        for work_info in success_lists
    }

    job_positions = {jp.job_position: jp for jp in JobPosition.objects.all()}
    existing_job_roles = {
        (jr.job_role, jr.job_position_id): jr for jr in JobRole.objects.all()
    }

    job_role_obj_list = []

    for job_role, job_position_name in job_roles_to_import:

        if not job_role or not job_position_name:
            continue

        job_position_obj = job_positions.get(job_position_name)
        if not job_position_obj:
            continue

        if (job_role, job_position_obj.id) not in existing_job_roles:
            job_role_obj = JobRole(job_position_id=job_position_obj, job_role=job_role)
            job_role_obj_list.append(job_role_obj)
            existing_job_roles[(job_role, job_position_obj.id)] = job_role_obj

    if job_role_obj_list:
        JobRole.objects.bulk_create(job_role_obj_list)


def bulk_create_work_types(success_lists):
    """
    Bulk creation of Job Position instances based on the excel import of employees
    """
    # Collect unique Job Positions
    work_types_to_import = {
        convert_nan("Job Position", work_info) for work_info in success_lists
    }
    work_types_to_import.discard(None)

    # Fetch existing Job Positions
    existing_work_types = {wt.work_type: wt for wt in WorkType.objects.all()}

    # Prepare list for new WorkType objects
    work_type_obj_list = [
        WorkType(work_type=work_type)
        for work_type in work_types_to_import
        if work_type not in existing_work_types
    ]
    # Bulk create new Job Positions
    if work_type_obj_list:
        WorkType.objects.bulk_create(work_type_obj_list)


def bulk_create_shifts(success_lists):
    """
    Bulk creation of shift instances based on the excel import of employees
    """
    # Collect unique shifts
    shifts_to_import = {convert_nan("Shift", work_info) for work_info in success_lists}
    shifts_to_import.discard(None)

    # Fetch existing shifts
    existing_shifts = {
        shift.employee_shift: shift for shift in EmployeeShift.objects.all()
    }

    # Prepare list for new EmployeeShift objects
    shift_obj_list = [
        EmployeeShift(employee_shift=shift)
        for shift in shifts_to_import
        if shift not in existing_shifts
    ]
    # Bulk create new shifts
    if shift_obj_list:
        EmployeeShift.objects.bulk_create(shift_obj_list)


def bulk_create_employee_types(success_lists):
    """
    Bulk creation of Employee Category instances based on the excel import of employees
    """
    # Collect unique Employee Categorys
    employee_types_to_import = {
        convert_nan("Employee Category", work_info) for work_info in success_lists
    }
    employee_types_to_import.discard(None)

    # Fetch existing Employee Categorys
    existing_employee_types = {
        et.employee_type: et for et in EmployeeType.objects.all()
    }

    # Prepare list for new EmployeeType objects
    employee_type_obj_list = [
        EmployeeType(employee_type=employee_type)
        for employee_type in employee_types_to_import
        if employee_type not in existing_employee_types
    ]
    # Bulk create new Employee Categorys
    if employee_type_obj_list:
        EmployeeType.objects.bulk_create(employee_type_obj_list)


def create_contracts_in_thread(new_work_info_list, update_work_info_list):
    """
    Creates employee contracts in bulk based on provided work information.
    """
    from payroll.models.models import Contract

    def get_or_none(value):
        return value if value else None

    contracts_list = [
        Contract(
            contract_name=f"{work_info.employee_id}'s Contract",
            employee_id=work_info.employee_id,
            contract_start_date=(
                work_info.date_joining if work_info.date_joining else datetime.today()
            ),
            department=get_or_none(work_info.department_id),
            job_position=get_or_none(work_info.job_position_id),
            job_role=get_or_none(work_info.job_role_id),
            shift=get_or_none(work_info.shift_id),
            work_type=get_or_none(work_info.work_type_id),
            wage=work_info.basic_salary or 0,
        )
        for work_info in new_work_info_list + update_work_info_list
        if work_info.employee_id
    ]

    Contract.objects.bulk_create(contracts_list)


def bulk_create_work_info_import(success_lists):
    """
    Bulk creation of employee work info instances based on the excel import of employees
    """
    new_work_info_list = []
    update_work_info_list = []

    # Filtered data for required lookups
    badge_ids = [row["Employee ID"] for row in success_lists]
    departments = set(row.get("Department") for row in success_lists)
    job_positions = set(row.get("Job Position") for row in success_lists)
    job_roles = set(row.get("Job Role") for row in success_lists)
    work_types = set(row.get("Work Type") for row in success_lists)
    employee_types = set(row.get("Employee Category") for row in success_lists)
    shifts = set(row.get("Shift") for row in success_lists)
    companies = set(row.get("Company") for row in success_lists)
    section = set(row.get("Employee Section") for row in success_lists)
    unit = set(row.get("Employee Unit") for row in success_lists)
    grade = set(row.get("Employee Grade") for row in success_lists)

    # Bulk fetch related objects and reduce repeated DB calls
    existing_employees = {
        emp.badge_id: emp
        for emp in Employee.objects.filter(badge_id__in=badge_ids).only("badge_id")
    }
    existing_employee_work_infos = {
        emp.employee_id: emp
        for emp in EmployeeWorkInformation.objects.filter(
            employee_id__in=existing_employees.values()
        ).only("employee_id")
    }
    existing_departments = {
        dep.department: dep
        for dep in Department.objects.filter(department__in=departments).only(
            "department"
        )
    }
    existing_job_positions = {
        (jp.department_id, jp.job_position): jp
        for jp in JobPosition.objects.filter(job_position__in=job_positions)
        .select_related("department_id")
        .only("department_id", "job_position")
    }

    existing_job_sections = {
        (jp.department_id, jp.employee_section): jp
        for jp in EmployeeSection.objects.filter(employee_section__in=section)
        .select_related("department_id")
        .only("department_id", "employee_section")
    }

    existing_job_units = {
        (jp.employee_section_id, jp.employee_unit): jp
        for jp in EmployeeUnit.objects.filter(employee_unit__in=unit)
        .select_related("employee_section_id")
        .only("employee_section_id", "employee_unit")
    }

    existing_job_roles = {
        (jr.job_position_id, jr.job_role): jr
        for jr in JobRole.objects.filter(job_role__in=job_roles)
        .select_related("job_position_id")
        .only("job_position_id", "job_role")
    }
    existing_work_types = {
        wt.work_type: wt
        for wt in WorkType.objects.filter(work_type__in=work_types).only("work_type")
    }
    existing_shifts = {
        es.employee_shift: es
        for es in EmployeeShift.objects.filter(employee_shift__in=shifts).only(
            "employee_shift"
        )
    }
    existing_employee_types = {
        et.employee_type: et
        for et in EmployeeType.objects.filter(employee_type__in=employee_types).only(
            "employee_type"
        )
    }
    existing_companies = {
        comp.company: comp
        for comp in Company.objects.filter(company__in=companies).only("company")
    }
    reporting_manager_dict = optimize_reporting_manager_lookup(success_lists)

    for work_info in success_lists:
        email = work_info["Employee Email(Official)"]
        badge_id = work_info["Employee ID"]
        department_obj = existing_departments.get(work_info.get("Department"))
        key = (
            existing_departments.get(work_info.get("Department")),
            work_info.get("Job Position"),
        )
        job_position_obj = existing_job_positions.get(key)
        job_role_obj = existing_job_roles.get(work_info.get("Job Role"))
        work_type_obj = existing_work_types.get(work_info.get("Work Type"))
        employee_type_obj = existing_employee_types.get(work_info.get("Employee Category"))
        shift_obj = existing_shifts.get(work_info.get("Shift"))
        employee_grade = work_info["Employee Grade"]
        reporting_manager = work_info.get("Reporting Manager")
        reporting_manager_obj = None
        if isinstance(reporting_manager, str) and " " in reporting_manager:
            if reporting_manager in reporting_manager_dict:
                reporting_manager_obj = reporting_manager_dict[reporting_manager]

        company_obj = existing_companies.get(work_info.get("Company"))
        location = work_info.get("Location")
        section_key = (
            existing_departments.get(work_info.get("Department")),
            work_info.get("Employee Section"),

        )
        section_obj = existing_job_sections.get(section_key)
        unit_key = (
            section_obj,
            work_info.get("Employee Unit"),
        )
        unit_obj = existing_job_units.get(unit_key)

        

        # Parsing dates and salary 
        date_joining = (
            work_info["Date Of Joining"]
            if not pd.isnull(work_info["Date Of Joining"])
            else datetime.today()
        )

        last_promotion_date = (
            work_info["Last Promotion Date"]
            if not pd.isnull(work_info["Last Promotion Date"])
            else datetime.today()
        )


        # contract_end_date = (
        #     work_info["Contract End Date"]
        #     if not pd.isnull(work_info["Contract End Date"])
        #     else None
        # )
        # basic_salary = (
        #     convert_nan("Basic Salary", work_info)
        #     if type(convert_nan("Basic Salary", work_info)) is int
        #     else 0
        # )
        # salary_hour = (
        #     convert_nan("Salary Hour", work_info)
        #     if type(convert_nan("Salary Hour", work_info)) is int
        #     else 0
        # )

        employee_obj = existing_employees.get(badge_id)
        employee_work_info = existing_employee_work_infos.get(employee_obj)

        if employee_work_info is None:
            print("newwork")
            # Create a new instance
            employee_work_info = EmployeeWorkInformation(
                employee_id=employee_obj,
                email=email,
                department_id=department_obj,
                job_position_id=job_position_obj,
                job_role_id=job_role_obj,
                work_type_id=work_type_obj,
                employee_type_id=employee_type_obj,
                shift_id=shift_obj,
                reporting_manager_id=reporting_manager_obj,
                company_id=company_obj,
                location=location,
                date_joining=(
                    date_joining if not pd.isnull(date_joining) else datetime.today()
                ),
                last_promotion_date=(
                    last_promotion_date if not pd.isnull(last_promotion_date) else datetime.today()
                ),
                employee_section_id=section_obj,
                employee_unit_id=unit_obj,
                employee_grade = employee_grade
                # contract_end_date=(
                #     contract_end_date if not pd.isnull(contract_end_date) else None
                # ),
                # basic_salary=basic_salary,
                # salary_hour=salary_hour,
            )
            new_work_info_list.append(employee_work_info)
        else:
            print("update work")
            # Update the existing instance
            employee_work_info.email = email
            employee_work_info.department_id = department_obj
            employee_work_info.job_position_id = job_position_obj
            employee_work_info.job_role_id = job_role_obj
            employee_work_info.work_type_id = work_type_obj
            employee_work_info.employee_type_id = employee_type_obj
            employee_work_info.shift_id = shift_obj
            employee_work_info.reporting_manager_id = reporting_manager_obj
            employee_work_info.company_id = company_obj
            employee_work_info.location = location 
            employee_work_info.date_joining = (
                date_joining if not pd.isnull(date_joining) else datetime.today()
            )
            employee_work_info.last_promotion_date = (
                last_promotion_date if not pd.isnull(last_promotion_date) else datetime.today()
            )
            employee_work_info.employee_section_id=section_obj
            employee_work_info.employee_unit_id = unit_obj
            employee_work_info.employee_grade = employee_grade
            # employee_work_info.contract_end_date = (
            #     contract_end_date if not pd.isnull(contract_end_date) else None
            # )
            # employee_work_info.basic_salary = basic_salary
            # employee_work_info.salary_hour = salary_hour
            update_work_info_list.append(employee_work_info)

    if new_work_info_list:
        EmployeeWorkInformation.objects.bulk_create(new_work_info_list)
    if update_work_info_list:
        EmployeeWorkInformation.objects.bulk_update(
            update_work_info_list,
            [
                "email",
                "department_id",
                "job_position_id",
                "job_role_id",
                "work_type_id",
                "employee_type_id",
                "shift_id",
                "reporting_manager_id",
                "company_id",
                "location",
                "date_joining",
                "last_promotion_date",
                "contract_end_date",
                "basic_salary",
                "salary_hour",
                "employee_section_id",
                "employee_unit_id",
                "employee_grade"
            ],
        )
    if apps.is_installed("payroll"):

        contract_creation_thread = threading.Thread(
            target=create_contracts_in_thread,
            args=(new_work_info_list, update_work_info_list),
        )
        contract_creation_thread.start()

def bulk_create_job_experience_info_import(success_lists):
     badge_ids = [row["Employee ID"] for row in success_lists]
     existing_employees = {
        emp.badge_id: emp
        for emp in Employee.objects.filter(badge_id__in=badge_ids).only("badge_id")
        }
     employee_obj = existing_employees.get(badge_id)
     experience1 = work_info["Job Experience 1"]
     experience2 = work_info["Job Experience 2"]
     experience3 = work_info["Job Experience 3"]
     experience4 = work_info["Job Experience 4"]
     #n_name,n_number,n_relation = [part.strip() for part in nominee.split(',')]
