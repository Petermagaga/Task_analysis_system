from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import User
from companies.models import Company, Department, WorkItem
from work_items.services import transition_work_item


class WorkItemTransitionTests(TestCase):

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST",
        )

        self.department = Department.objects.create(
            company=self.company,
            name="Production",
            code="PROD",
        )

        self.user = User.objects.create_user(
            username="employee",
            email="employee@test.com",
            password="TestPassword123!",
            company=self.company,
            department=self.department,
            role=User.Role.EMPLOYEE,
        )

        self.work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

    def test_draft_can_become_planned(self):
        transition_work_item(
            self.work_item,
            WorkItem.Status.PLANNED,
        )

        self.work_item.refresh_from_db()

        self.assertEqual(
            self.work_item.status,
            WorkItem.Status.PLANNED,
        )

    def test_planned_can_become_in_progress(self):
        transition_work_item(
            self.work_item,
            WorkItem.Status.PLANNED,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.IN_PROGRESS,
        )

        self.work_item.refresh_from_db()

        self.assertEqual(
            self.work_item.status,
            WorkItem.Status.IN_PROGRESS,
        )

    def test_draft_cannot_become_completed(self):
        with self.assertRaises(ValidationError):
            transition_work_item(
                self.work_item,
                WorkItem.Status.COMPLETED,
            )

    def test_cancelled_work_cannot_be_completed(self):
        transition_work_item(
            self.work_item,
            WorkItem.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            transition_work_item(
                self.work_item,
                WorkItem.Status.COMPLETED,
            )

    def test_completed_can_be_reviewed(self):
        transition_work_item(
            self.work_item,
            WorkItem.Status.PLANNED,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.IN_PROGRESS,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.COMPLETED,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.REVIEWED,
        )

        self.work_item.refresh_from_db()

        self.assertEqual(
            self.work_item.status,
            WorkItem.Status.REVIEWED,
        )

    def test_reviewed_can_be_archived(self):
        transition_work_item(
            self.work_item,
            WorkItem.Status.PLANNED,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.IN_PROGRESS,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.COMPLETED,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.REVIEWED,
        )

        transition_work_item(
            self.work_item,
            WorkItem.Status.ARCHIVED,
        )

        self.work_item.refresh_from_db()

        self.assertEqual(
            self.work_item.status,
            WorkItem.Status.ARCHIVED,
        )

    def test_archived_work_cannot_change(self):
        transition_work_item(
            self.work_item,
            WorkItem.Status.CANCELLED,
        )

        with self.assertRaises(ValidationError):
            transition_work_item(
                self.work_item,
                WorkItem.Status.PLANNED,
            )