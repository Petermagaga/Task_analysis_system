import uuid

from django.db import models
from django.core.exceptions import ValidationError

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
        constraints=[
            models.UniqueConstraint(
                fields=["company","code"],
                name="unique_department_code_per_company",),
        ]
    def __str__(self):
        return f"{self.name} ({self.company.code})"

class WorkSchedule(models.Model):
    """
    Defines thenormal working schedule for a company.
    """
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,
                        editable=False)
    company=models.ForeignKey(Company,on_delete=models.PROTECT,related_name="work_schedules",)
    name=models.CharField(
        max_length=150,
    )
    timezone=models.CharField(max_length=150,default="Africa/Nairobi",)
    start_time=models.TimeField()
    end_time=models.TimeField()
    break_start=models.TimeField()
    break_end=models.TimeField()
    working_days=models.JSONField(
        default=list,
    )
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
        
    def clean(self):
        errors = {}

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                errors["end_time"] = (
                    "End time must be later than start time."
                )

        if self.break_start and self.break_end:
            if self.break_start >= self.break_end:
                errors["break_end"] = (
                    "Break end time must be later than break start time."
                )

        if self.break_start and self.start_time:
            if self.break_start < self.start_time:
                errors["break_start"] = (
                    "Break must start after the working day starts."
                )

        if self.break_end and self.end_time:
            if self.break_end > self.end_time:
                errors["break_end"] = (
                    "Break must end before the working day ends."
                )

        if bool(self.break_start) != bool(self.break_end):
            errors["break_start"] = (
                "Break start and break end must both be provided."
            )

        if not self.working_days:
            errors["working_days"] = (
                "At least one working day must be selected."
            )

        invalid_days = [
            day
            for day in self.working_days
            if not isinstance(day, int) or day < 0 or day > 6
        ]

        if invalid_days:
            errors["working_days"] = (
                "Working days must contain integers from 0 to 6."
            )

        if errors:
            raise ValidationError(errors)



    class Meta:
        ordering=["name"]

    def __str__(self):
        return f"{self.name} ({self.company.code})"

class WorkItem(models.Model):

    class WorkType(models.TextChoices):
        TASK = "TASK", "Task"
        MEETING = "MEETING", "Meeting"
        ROUTINE = "ROUTINE", "Routine"
        SUPPORT = "SUPPORT", "Support"
        TRAINING = "TRAINING", "Training"
        PROJECT = "PROJECT", "Project"
        INCIDENT = "INCIDENT", "Incident"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PLANNED = "PLANNED", "Planned"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        PARTIALLY_COMPLETED = "PARTIALLY_COMPLETED", "Partially Completed"
        COMPLETED = "COMPLETED", "Completed"
        BLOCKED = "BLOCKED", "Blocked"
        DEFERRED = "DEFERRED", "Deferred"
        CANCELLED = "CANCELLED", "Cancelled"
        REVIEWED = "REVIEWED", "Reviewed"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="work_items",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="work_items",
    )

    owner = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="owned_work_items",
    )

    title = models.CharField(max_length=255)

    description = models.TextField(blank=True)

    work_type = models.CharField(
        max_length=30,
        choices=WorkType.choices,
        default=WorkType.TASK,
    )

    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    planned_at = models.DateTimeField()

    due_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        # ---------------------------------------------------------
        # 1. Due date cannot be before planned date
        # ---------------------------------------------------------
        if self.due_at and self.planned_at:
            if self.due_at < self.planned_at:
                errors["due_at"] = (
                    "Due date and time cannot be earlier "
                    "than the planned date and time."
                )

        # ---------------------------------------------------------
        # 2. Department must belong to the same company
        # ---------------------------------------------------------
        if self.company_id and self.department_id:
            if self.department.company_id != self.company_id:
                errors["department"] = (
                    "Department must belong to the same company "
                    "as the work item."
                )

        # ---------------------------------------------------------
        # 3. Owner must belong to the same company
        # ---------------------------------------------------------
        if self.company_id and self.owner_id:
            if self.owner.company_id != self.company_id:
                errors["owner"] = (
                    "Owner must belong to the same company "
                    "as the work item."
                )

        # ---------------------------------------------------------
        # 4. Owner's department must match WorkItem department
        # ---------------------------------------------------------
        if self.department_id and self.owner_id:
            if self.owner.department_id != self.department_id:
                errors["owner"] = (
                    "Owner must belong to the same department "
                    "as the work item."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return self.title

class WorkExecution(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="work_executions",
    )

    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.PROTECT,
        related_name="executions",
    )

    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="work_executions",
    )

    started_at = models.DateTimeField()

    ended_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def clean(self):
        errors = {}

        # ---------------------------------------------------------
        # 1. End time cannot be before start time
        # ---------------------------------------------------------
        if self.ended_at and self.started_at:
            if self.ended_at < self.started_at:
                errors["ended_at"] = (
                    "End time cannot be earlier than start time."
                )

        # ---------------------------------------------------------
        # 2. Execution company must match WorkItem company
        # ---------------------------------------------------------
        if self.company_id and self.work_item_id:
            if self.work_item.company_id != self.company_id:
                errors["company"] = (
                    "Execution must belong to the same company "
                    "as the work item."
                )

        # ---------------------------------------------------------
        # 3. Employee must belong to execution company
        # ---------------------------------------------------------
        if self.company_id and self.employee_id:
            if self.employee.company_id != self.company_id:
                errors["employee"] = (
                    "Employee must belong to the same company "
                    "as the execution."
                )

        if errors:
            raise ValidationError(errors)

    @property
    def duration(self):
        if not self.ended_at:
            return None
        return self.ended_at-self.started_at

    def __str__(self):
        return (
            f"{self.work_item.title} - "
            f"{self.employee}"
        ) 

class Outcome(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="outcomes",
    )

    work_item = models.ForeignKey(
        WorkItem,
        on_delete=models.PROTECT,
        related_name="outcomes",
    )

    employee = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="outcomes",
    )

    description = models.TextField()

    is_confirmed = models.BooleanField(
        default=False,
    )

    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    def clean(self):
        errors = {}

        if self.company_id and self.work_item_id:
            if self.work_item.company_id != self.company_id:
                errors["company"] = (
                    "Outcome must belong to the same company "
                    "as the work item."
                )

        if self.company_id and self.employee_id:
            if self.employee.company_id != self.company_id:
                errors["employee"] = (
                    "Employee must belong to the same company "
                    "as the outcome."
                )

        if self.is_confirmed and not self.confirmed_at:
            errors["confirmed_at"] = (
                "Confirmed outcomes must have a confirmation time."
            )

        if not self.is_confirmed and self.confirmed_at:
            errors["confirmed_at"] = (
                "Unconfirmed outcomes cannot have a confirmation time."
            )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return (
            f"{self.work_item.title} - "
            f"{self.employee}"
        )    





