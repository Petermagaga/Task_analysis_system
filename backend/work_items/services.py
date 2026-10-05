from django.core.exceptions import ValidationError


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