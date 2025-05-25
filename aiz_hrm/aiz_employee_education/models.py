
from django.db import models
from django.utils.translation import gettext as _
from employee.models import Employee
from aiz.models import aizModel
from django.utils.translation import gettext_lazy as trans


def employee_education_create(instance):
    employees = instance.employee_id.all()
    for employee in employees:
        employee_education = EmployeeEducation.objects.get_or_create(
            employee_id=employee,
            defaults={"education_label": f"Employee Education {instance.education_label}"},
        )
        employee_education[0].education_label = f"Employee Education {instance.education_label}"
        employee_education[0].save()

class EmployeeEducation(aizModel):
    """
    EmployeeEducation model
    """
    choice_education = [
    ("primary", trans("Primary Education")),
    ("jsc", trans("Junior School Certificate")),
    ("ssc", trans("Secondary School Certificate")),
    ("dakhil", trans("Dakhil (Madrasa)")),
    ("hsc", trans("Higher Secondary Certificate")),
    ("alim", trans("Alim (Madrasa)")),
    ("diploma", trans("Diploma in Engineering")),
    ("vocational", trans("Technical/Vocational")),
    ("fazil", trans("Fazil (Madrasa)")),
    ("bachelor", trans("Bachelor Degree")),
    ("honours", trans("Honours Degree")),
    ("pass", trans("Pass Course")),
    ("masters", trans("Masters Degree")),
    ("kamil", trans("Kamil (Madrasa)")),
    ("mphil", trans("MPhil")),
    ("phd", trans("PhD")),
    
    
    
    
    
]

    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name="educations")
    education_label = models.CharField(
        max_length=50, blank=True, null=True, choices=choice_education, default="primary"
    )
    institution_name = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Institution name")
    )
    subject = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Subject")
    )
    passing_year = models.CharField(
        max_length=200, null=True, blank=True, verbose_name=_("Passing year")
    )

    def __str__(self) -> str:
        return f"{self.employee_id}-{self.education_label}"

    

    def upload_documents_count(self):
        total_requests = EmployeeEducation.objects.filter(
            employee_id=self.employee_id
        )
        count = total_requests.count()
        return count


from django.db import models

# Create your models here.
