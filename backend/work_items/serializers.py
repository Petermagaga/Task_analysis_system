from rest_framework import serializers

from companies.models import WorkItem

class WorkItemSerializer(serializers.ModelSerializer):
    class Meta:
        model=WorkItem
        fields =[
            "id","department","title","description","work_type","planned_at","due_at","status","created_at","uploaded_at"
        ]
        read_only_fields=[
            "id",
            "status",
            "created_at",
            "updated_at",
        ]

    def validate_department(self,department):
        request= self.context.get("request")

        if request and department.company_id !=request.user.company_id:
            raise serializers.ValidationError(
                "You can only assign work to a department in your company."
            )

        if not department.is_active:
            raise serializers.ValidationError(
                "You cannot assign work to an Inactive department"

    
            )
        return department

    def validate(self,attrs):
        planned_at = attrs.get("planned_at")
        due_at = attrs.get("due_at")

        if planned_at and due_at and due_at<planned_at:
            raise serializers.ValidationError(
                {
                    "due_at":"DUE date and time cannot be earlier than planned time."                }
            )
        return attrs