from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import generics,serializers,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from companies.models import WorkItem,WorkExecution,Outcome
from .serializers import WorkItemSerializer,WorkExecutionSerializer,OutcomeSerializer
from .services import (transition_work_item,start_execution,stop_execution,create_outcome,confirm_outcome)

class WorkItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = WorkItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = WorkItem.objects.filter(
            company_id=user.company_id
        )

        if user.role == "EMPLOYEE":
            queryset = queryset.filter(owner=user)

        elif user.role == "SUPERVISOR":
            queryset = queryset.filter(
                department_id=user.department_id
            )

        # Managers and admins can see company work items.
        return (
            queryset
            .select_related("department", "owner")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        user = self.request.user

        serializer.save(
            company=user.company,
            owner=user,
            department=user.department,
            status=WorkItem.Status.DRAFT,
        )



password="UniquePassword123!"

password2="ReplaceWithYourOwnStrongTestPassword!"

class WorkItemTransitionAPIView(APIView):
    permission_classes =[IsAuthenticated]

    def post(self,request,work_item_id):
        user=request.user
        #Begin with records belonging to the user's company

        queryset= WorkItem.objects.filter(
            company_id=user.company_id
        )

        #apply the same visibility boundaries as the list

        if user.role=="EMPLOYEE":
            queryset=queryset.filter(owner=user)
        elif user.role== "SUPERVISOR":
            queryset=queryset.filter(
                department_id=user.department_id
            )
        work_item=get_object_or_404(queryset,
                                    id=work_item_id,)

        new_status=request.data.get("status")

        if not isinstance(new_status,str) or not new_status:
            raise serializers.ValidationError({
                "status":"A target status is required."
            })

        try:
            work_item=transition_work_item(work_item,
                                           new_status,)

        except DjangoValidationError as exc:
            detail =(
                exc.message_dict
                if hasattr(exc,'message_dict')
                else exc.messages
            )
            raise serializers.ValidationError(detail) from exc

        return Response({
            "id":str(work_item.id),
            "title":work_item.title,
            "status":work_item.status,
        },
        status=status.HTTP_200_OK,
        )



class WorkExecutionStartAPIView(APIView):
    permission_classes=[IsAuthenticated]

    def post(self,request,work_item_id):
        user=request.user

        queryset=WorkItem.objects.filter(
            company_id=user.company_id,
        )

        if user.role =="EMPLOYEE":
            queryset=queryset.filter(owner=user)
        elif user.role =="SUPERVISOR":
            queryset=queryset.filter(department_id=user.department_id,)

        work_item=get_object_or_404(queryset,id=work_item_id)

        notes=request.data.get("notes","")

        if not isinstance(notes,str):
            raise serializers.ValidationError({"notes":"Notes must be text."})
        try:
            execution=start_execution(
                work_item=work_item,
                employee=user,
                notes=notes,
            )
        except DjangoValidationError as exc:
            detail=(
                exc.message_dict
                if hasattr(exc,"message_dict")
                else exc.messages
            )

            raise serializers.ValidationError(detail) from exc

        return Response(
            WorkExecutionSerializer(execution).data,
            status=status.HTTP_201_CREATED
        )


class WorkExecutionStopAPIView(APIView):
    permission_classes=[IsAuthenticated]
    
    def post(self,request,execution_id):
        user=request.user
        queryset=WorkExecution.objects.filter(company_id=user.company_id,)

        if user.role=="EMPLOYEE":
            queryset=queryset.filter(employee=user)
        elif user.role=="SUPERVISOR":
            queryset=queryset.filter(work_item__department_id=user.department_id,)

        execution =get_object_or_404(queryset, id=execution_id)

        try:
            execution=stop_execution(execution)

        except DjangoValidationError as exc:
            detail=(
                exc.message_dict
                if hasattr(exc,"message_dict")
                           else exc.messages
            )
            raise serializers.ValidationError(detail) from exc

        return Response(
            WorkExecutionSerializer(execution).data,
            status=status.HTTP_200_OK,
        )

class WorkItemOutcomeCreateAPIView(APIView):
    permission_classes =[IsAuthenticated]

    def post(self,request,work_item_id):
        user=request.user

        #Employees may record outcomes only for their own work

        work_item=get_object_or_404(
            WorkItem.objects.filter(
                company_id=user.company_id,
                owner=user,
            ),
            id=work_item_id,
        )

        description=request.data.get("description","")

        if not isinstance(description,str):
            raise serializers.ValidationError(
                {
                    "description":"Description must be text"
                }
            )
        try:
            outcome=create_outcome(
                work_item=work_item,
                employee=user,
                description=description
            )

        except DjangoValidationError as exc:
            detail=(
                exc.message_dict
                if hasattr(exc,"message_dict")
                else exc.messages
            )
            raise serializers.ValidationError(detail) from exc

        return Response(
            OutcomeSerializer(outcome).data,
            status=status.HTTP_201_CREATED,
        )


    