
from django.db import models
from django.utils.translation import gettext as _
from employee.models import Employee
from aiz.models import aizModel


def employee_training_create(instance):
    employees = instance.employee_id.all()
    for employee in employees:
        employee_training = EmployeeTraining.objects.get_or_create(
            employee_id=employee,
            defaults={"training_name": f"Employee Training {instance.training_name}"},
        )
        employee_training[0].training_name = f"Employee Training {instance.training_name}"
        employee_training[0].save()

class EmployeeTraining(aizModel):
    """
    EmployeeTraining model
    """

    employee_id = models.ForeignKey(Employee, on_delete=models.PROTECT)
    training_name = models.CharField(max_length=200,null=False,blank=False,default="",)
    institution = models.CharField(max_length=100,null=False,blank=False,default="",)

    def __str__(self) -> str:
        return f"{self.employee_id}-{self.training_name}"

    

    def upload_documents_count(self):
        total_requests = EmployeeTraining.objects.filter(
            employee_id=self.employee_id
        )
        count = total_requests.count()
        return count


from django.db import models

# Create your models here.
