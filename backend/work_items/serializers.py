
from rest_framework import serializers

from companies.models import WorkItem
from 

class WorkItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkItem
        fields = [
            "id",
            "department",
            "title",
            "description",
            "work_type",
            "planned_at",
            "due_at",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_department(self, department):
        request = self.context.get("request")

        if request is None:
            return department

        user = request.user

        if department.company_id != user.company_id:
            raise serializers.ValidationError(
                "You can only use a department in your company."
            )

        if not department.is_active:
            raise serializers.ValidationError(
                "You cannot assign work to an inactive department."
            )

        if user.department_id is None:
            raise serializers.ValidationError(
                "Your account must have a department before "
                "you can create a work item."
            )

        if department.id != user.department_id:
            raise serializers.ValidationError(
                "You can only create work items in your own department."
            )

        return department

    def validate(self, attrs):
        planned_at = attrs.get("planned_at")
        due_at = attrs.get("due_at")

        if (
            planned_at is not None
            and due_at is not None
            and due_at < planned_at
        ):
            raise serializers.ValidationError({
                "due_at": (
                    "Due date and time cannot be earlier "
                    "than the planned time."
                )
            })

        return attrs
