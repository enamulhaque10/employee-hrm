
from django.db import models
from django.utils.translation import gettext as _
from employee.models import Employee
from aiz.models import aizModel


def job_experience_create(instance):
    employees = instance.employee_id.all()
    for employee in employees:
        job_experience = JobReference.objects.get_or_create(
            employee_id=employee,
            defaults={"title": f"Job Reference {instance.reference_name}"},
        )
        job_experience[0].reference_name = f"Job Reference {instance.reference_name}"
        job_experience[0].save()

class JobReference(aizModel):
    """
    JobReference model
    """

    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT)
    reference_name = models.CharField(max_length=150,null=False,blank=False,default="",)
    department = models.CharField(max_length=150,null=False,blank=False,default="",)
    company_name = models.CharField(max_length=150,null=False,blank=False,default="",)
    mobile_number = models.CharField(max_length=50,null=False,blank=False,default="",)

    def __str__(self) -> str:
        return f"{self.employee_id}-{self.company_name}"

    

    def upload_documents_count(self):
        total_requests = JobReference.objects.filter(
            employee_id=self.employee_id
        )
        count = total_requests.count()
        return count


from django.db import models

# Create your models here.
