import uuid

from django.db import models

class Company(models.Model):
    """
    Tenant/root organization in the system
    Every major business record will ultimately belong to acompany
    
    """
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=200,)
    code=models.CharField(max_length=50,unique=True,)
    email=models.EmailField(blank=True,)
    phone=models.CharField(max_length=50,blank=True,)
    address=models.TextField(blank=True,)
    timezone=models.CharField(max_length=64,default="Africa/nairobi",)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True,)
    updated_at=models.DateTimeField(auto_now=True)

    class Meta:
        ordering=["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Department(models.Model):
    """
    Organizational department belonging to a company
    """
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    company=models.ForeignKey(Company,on_delete=models.PROTECT,related_name="departments",)
    name=models.CharField(max_length=150)
    code=models.CharField(max_length=50)
    description=models.TextField(
        blank=True
    )
    is_active=models.BooleanField(default=True)
    created_at= models.DateTimeField(auto_now_add=True,)
    updated_at=models.DateTimeField(auto_now=True,)

    class Meta:
        ordering=["name"]
        contraints=[
            models.UniqueConstraint(fields=["company","code"],
                                    name="unique_department_code_per_company",),
        ]
    def __str__(self):
        return f"{self.name} ({self.company.code})"

