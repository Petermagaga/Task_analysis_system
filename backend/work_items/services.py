from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from companies.models import WorkExecution,Outcome

STATUS_TRANSITIONS = {
    "DRAFT": {
        "PLANNED",
        "CANCELLED",
    },

    "PLANNED": {
        "IN_PROGRESS",
        "DEFERRED",
        "CANCELLED",
    },

    "IN_PROGRESS": {
        "PARTIALLY_COMPLETED",
        "COMPLETED",
        "BLOCKED",
        "DEFERRED",
        "CANCELLED",
    },

    "PARTIALLY_COMPLETED": {
        "IN_PROGRESS",
        "COMPLETED",
        "BLOCKED",
        "DEFERRED",
        "CANCELLED",
    },

    "BLOCKED": {
        "IN_PROGRESS",
        "DEFERRED",
        "CANCELLED",
    },

    "DEFERRED": {
        "PLANNED",
        "CANCELLED",
    },

    "COMPLETED": {
        "REVIEWED",
    },

    "REVIEWED": {
        "ARCHIVED",
    },

    "CANCELLED": set(),

    "ARCHIVED": set(),
}


def transition_work_item(work_item, new_status):
    current_status = work_item.status

    allowed_statuses = STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValidationError(
            {
                "status": (
                    f"Cannot transition work item from "
                    f"{current_status} to {new_status}."
                )
            }
        )

    work_item.status = new_status
    work_item.save(update_fields=["status", "updated_at"])

    return work_item

@transaction.atomic
def start_execution(work_item,employee,started_at=None,notes="",):
    if work_item.company_id !=employee.company_id:
        raise ValidationError(
            {
                "employee":(
                    "Employee must belong to the same company"
                    "as the work item."
                )
            }
        )
    allowed_statuses={
        "PLANNED",
        "IN_PROGRESS",
        "PARTIALLY_COMPLETED",
        "BLOCKED",
    }
    if work_item.status not in allowed_statuses:
        raise ValidationError(
            {
                "status":(
                    f"Cannot start execution for a work item "
                    f"with status {work_item.status}"
                )
            }
        )

    if started_at is None:
        started_at=timezone.now()

    execution=WorkExecution(
        company=work_item.company,
        work_item=work_item,
        employee=employee,
        started_at=started_at,
        notes=notes,
    )
    execution.full_clean()
    execution.save()

    if work_item.status !="IN_PROGRESS":
        transition_work_item(
            work_item,
            "IN_PROGRESS",

        )
        return execution
@transaction.atomic
def stop_execution(execution,ended_at=None,):

    if execution.ended_at is not None:
        raise ValidationError(
            {
                "ended_at":(
                    "This execution has already been stopped."
                )
            }
        )
    if ended_at is None:
        ended_at=timezone.now()

    if ended_at<execution.started_at:
        raise ValidationError(
            {
                "ended_at":(
                    "End time cannot be earlier than"
                    "start time"
                )
            }
        )
    execution.ended_at=ended_at
    execution.full_clean()
    execution.save(
        update_fields=[
            "ended_at",
            "updated_at"
        ]
    )
    return execution

@transaction.atomic
def create_outcome(work_item,employee,description,):
    if work_item.company_id !=employee.company_id:
        raise ValidationError(
            {
                "employee":(
                    "Employee must belong to the same company "
                    "as the work item."
                )
            }
        )
    if not description or not description.strip():
        raise ValidationError(
            {
                "Description":(
                    "Outcome description cannot be empty."
                )
            }
        )
    outcome=Outcome(
        company=work_item.company,
        work_item=work_item,
        employee=employee,
        description=description.strip(),
    )

    outcome.full_clean()
    outcome.save()

    return outcome


@transaction.atomic
def confirm_outcome(outcome,confirmed_at=None,):
    if outcome.is_confirmed:
        raise ValidationError(
            {
                "is_confirmed":("This outcome has already been confirmed.")
            }
        )
    if confirmed_at is None:
        confirmed_at=timezone.now()

    outcome.is_confirmed=True
    outcome.confirmed_at=confirmed_at

    outcome.full_clean()

    outcome.save(
        update_fields=[
            "is_confirmed",
            "confirmed_at",
            "updated_at",
        ]
    )
    return outcome


@transaction.atomic
def attach_execution_to_outcome(outcome,execution):
    if outcome.company_id != execution.company_id:
        raise ValidationError(

            {
                "execution":(
                    "Execution must belong to the same "
                    "company as the outcome"
                )
            }
        )
    if outcome.work_item_id != execution.work_item_id:
        raise ValidationError(
            {
                "execution":(
                    "execution must belong to same "
                    "work item as the outcome"
                )
            }
        )
    outcome.executions.add(execution)

    return outcome
