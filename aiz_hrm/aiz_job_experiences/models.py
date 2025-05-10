
from django.db import models
from django.utils.translation import gettext as _
from employee.models import Employee
from aiz.models import aizModel


def job_experience_create(instance):
    employees = instance.employee_id.all()
    for employee in employees:
        job_experience = EmployeeJobExperiences.objects.get_or_create(
            employee_id=employee,
            defaults={"title": f"Job Experience {instance.title}"},
        )
        job_experience[0].title = f"Job Experience {instance.title}"
        job_experience[0].save()

class EmployeeJobExperiences(aizModel):
    """
    EmployeeJobExperiences model
    """

    title = models.CharField(max_length=250)
    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT)
    company_name = models.CharField(max_length=50,null=True,blank=True,default="",)
    designation = models.CharField(max_length=50,null=False,blank=False,default="",)
    year_of_experience = models.FloatField(default=0, help_text="Employee Year Of Experience.")

    def __str__(self) -> str:
        return f"{self.employee_id}-{self.company_name}"

    

    def upload_documents_count(self):
        total_requests = EmployeeJobExperiences.objects.filter(
            employee_id=self.employee_id
        )
        count = total_requests.count()
        return count


from django.db import models

# Create your models here.
