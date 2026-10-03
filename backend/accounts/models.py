from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    APPLICATION USER.
    A user belongs to one company in V1
    """

    class Role(models.TextChoices):
        EMPLOYEE="EMPLOYEE","Employee"
        SUPERVISOR="SUPERVISOR","Supervisor"
        MANAGER="MANAGER","Manager"
        ADMIN="ADMIN","Admin"


    email=models.EmailField(unique=True,)
    employee_number=models.CharField(
        max_length=50,
        blank=True,
    )
    department=models.ForeignKey("companies.Department",on_delete=models.PROTECT,
                                 related_name="users",null=True,blank=True,)
    company=models.ForeignKey("companies.Company",on_delete=models.PROTECT,related_name="users",)
    role=models.CharField(max_length=20,choices=Role.choices,
                            default=Role.EMPLOYEE)
    position=models.CharField(max_length=150,blank=True)
    phone=models.CharField(max_length=50,blank=True)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True,)

    def __str__(self):
        return self.get_full_name() or self.email
    