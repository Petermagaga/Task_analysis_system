from datetime import datetime
from zoneinfo import ZoneInfo
from django.core.exceptions import ValidationError
from django.test import TestCase
from accounts.models import User
from companies.models import Company, Department, WorkItem,Outcome
from work_items.services import (transition_work_item,
                                 start_execution,
                                 stop_execution,confirm_outcome,
                                 create_outcome,attach_execution_to_outcome,WorkExecution)


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

        planned_time = datetime(
            2026,
            10,
            4,
            8,
            0,
            tzinfo=ZoneInfo("Africa/Nairobi"),
        )

        self.work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at=planned_time,
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

class WorkExecutionServiceTests(TestCase):

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

        self.employee = User.objects.create_user(
            username="employee",
            email="employee@test.com",
            password="TestPassword123!",
            company=self.company,
            department=self.department,
            role=User.Role.EMPLOYEE,
            first_name="Test",
            last_name="Employee",
        )

        self.work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.employee,
            title="Repair stitching machine",
            planned_at=datetime(
                2026,
                10,
                6,
                8,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
            status=WorkItem.Status.PLANNED,
        )

    def test_start_execution_creates_active_execution(self):
        started_at = datetime(
            2026,
            10,
            6,
            8,
            15,
            tzinfo=ZoneInfo("Africa/Nairobi"),
        )

        execution = start_execution(
            work_item=self.work_item,
            employee=self.employee,
            started_at=started_at,
        )

        self.assertIsNotNone(execution.id)
        self.assertEqual(execution.employee, self.employee)
        self.assertEqual(execution.work_item, self.work_item)
        self.assertEqual(execution.started_at, started_at)
        self.assertIsNone(execution.ended_at)

    def test_start_execution_moves_work_item_to_in_progress(self):
        start_execution(
            work_item=self.work_item,
            employee=self.employee,
            started_at=datetime(
                2026,
                10,
                6,
                8,
                15,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        self.work_item.refresh_from_db()

        self.assertEqual(
            self.work_item.status,
            WorkItem.Status.IN_PROGRESS,
        )

    def test_start_execution_rejects_employee_from_another_company(self):
        other_company = Company.objects.create(
            name="Other Company",
            code="OTHER",
        )

        other_department = Department.objects.create(
            company=other_company,
            name="Operations",
            code="OPS",
        )

        other_employee = User.objects.create_user(
            username="other_employee",
            email="other@test.com",
            password="TestPassword123!",
            company=other_company,
            department=other_department,
            role=User.Role.EMPLOYEE,
        )

        with self.assertRaises(ValidationError):
            start_execution(
                work_item=self.work_item,
                employee=other_employee,
            )

    def test_draft_work_item_cannot_start_execution(self):
        self.work_item.status = WorkItem.Status.DRAFT
        self.work_item.save(
            update_fields=["status", "updated_at"]
        )

        with self.assertRaises(ValidationError):
            start_execution(
                work_item=self.work_item,
                employee=self.employee,
            )

    def test_stop_execution_sets_end_time(self):
        started_at = datetime(
            2026,
            10,
            6,
            8,
            15,
            tzinfo=ZoneInfo("Africa/Nairobi"),
        )

        ended_at = datetime(
            2026,
            10,
            6,
            9,
            0,
            tzinfo=ZoneInfo("Africa/Nairobi"),
        )

        execution = start_execution(
            work_item=self.work_item,
            employee=self.employee,
            started_at=started_at,
        )

        stop_execution(
            execution=execution,
            ended_at=ended_at,
        )

        execution.refresh_from_db()

        self.assertEqual(
            execution.ended_at,
            ended_at,
        )

        self.assertEqual(
            execution.duration.total_seconds(),
            45 * 60,
        )

    def test_execution_cannot_be_stopped_twice(self):
        execution = start_execution(
            work_item=self.work_item,
            employee=self.employee,
            started_at=datetime(
                2026,
                10,
                6,
                8,
                15,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        stop_execution(
            execution=execution,
            ended_at=datetime(
                2026,
                10,
                6,
                9,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        with self.assertRaises(ValidationError):
            stop_execution(
                execution=execution,
                ended_at=datetime(
                    2026,
                    10,
                    6,
                    9,
                    30,
                    tzinfo=ZoneInfo("Africa/Nairobi"),
                ),
            )

    def test_stop_execution_rejects_end_before_start(self):
        execution = start_execution(
            work_item=self.work_item,
            employee=self.employee,
            started_at=datetime(
                2026,
                10,
                6,
                9,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        with self.assertRaises(ValidationError):
            stop_execution(
                execution=execution,
                ended_at=datetime(
                    2026,
                    10,
                    6,
                    8,
                    0,
                    tzinfo=ZoneInfo("Africa/Nairobi"),
                ),
            )


class OutcomeServiceTests(TestCase):

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

        self.employee = User.objects.create_user(
            username="employee",
            email="employee@test.com",
            password="TestPassword123!",
            company=self.company,
            department=self.department,
            role=User.Role.EMPLOYEE,
            first_name="Test",
            last_name="Employee",
        )

        self.work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.employee,
            title="Repair stitching machine",
            planned_at=datetime(
                2026,
                10,
                7,
                8,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
            status=WorkItem.Status.IN_PROGRESS,
        )

    def test_create_outcome_creates_unconfirmed_outcome(self):
        outcome = create_outcome(
            work_item=self.work_item,
            employee=self.employee,
            description="Machine repaired successfully.",
        )

        self.assertIsNotNone(outcome.id)
        self.assertEqual(
            outcome.work_item,
            self.work_item,
        )
        self.assertEqual(
            outcome.employee,
            self.employee,
        )
        self.assertEqual(
            outcome.description,
            "Machine repaired successfully.",
        )
        self.assertFalse(outcome.is_confirmed)
        self.assertIsNone(outcome.confirmed_at)

    def test_create_outcome_strips_description(self):
        outcome = create_outcome(
            work_item=self.work_item,
            employee=self.employee,
            description="  Machine repaired successfully.  ",
        )

        self.assertEqual(
            outcome.description,
            "Machine repaired successfully.",
        )

    def test_create_outcome_rejects_empty_description(self):
        with self.assertRaises(ValidationError):
            create_outcome(
                work_item=self.work_item,
                employee=self.employee,
                description="   ",
            )

    def test_create_outcome_rejects_employee_from_another_company(self):
        other_company = Company.objects.create(
            name="Other Company",
            code="OTHER",
        )

        other_department = Department.objects.create(
            company=other_company,
            name="Operations",
            code="OPS",
        )

        other_employee = User.objects.create_user(
            username="other_employee",
            email="other@test.com",
            password="TestPassword123!",
            company=other_company,
            department=other_department,
            role=User.Role.EMPLOYEE,
        )

        with self.assertRaises(ValidationError):
            create_outcome(
                work_item=self.work_item,
                employee=other_employee,
                description="Machine repaired.",
            )

    def test_confirm_outcome_confirms_outcome(self):
        outcome = create_outcome(
            work_item=self.work_item,
            employee=self.employee,
            description="Machine repaired successfully.",
        )

        confirmed_at = datetime(
            2026,
            10,
            7,
            9,
            30,
            tzinfo=ZoneInfo("Africa/Nairobi"),
        )

        confirm_outcome(
            outcome=outcome,
            confirmed_at=confirmed_at,
        )

        outcome.refresh_from_db()

        self.assertTrue(outcome.is_confirmed)
        self.assertEqual(
            outcome.confirmed_at,
            confirmed_at,
        )

    def test_confirm_outcome_uses_current_time_when_not_provided(self):
        outcome = create_outcome(
            work_item=self.work_item,
            employee=self.employee,
            description="Machine repaired successfully.",
        )

        confirm_outcome(outcome)

        outcome.refresh_from_db()

        self.assertTrue(outcome.is_confirmed)
        self.assertIsNotNone(outcome.confirmed_at)

    def test_confirm_outcome_cannot_be_done_twice(self):
        outcome = create_outcome(
            work_item=self.work_item,
            employee=self.employee,
            description="Machine repaired successfully.",
        )

        confirm_outcome(outcome)

        with self.assertRaises(ValidationError):
            confirm_outcome(outcome)

    def test_confirm_outcome_does_not_complete_work_item(self):
        outcome = create_outcome(
            work_item=self.work_item,
            employee=self.employee,
            description="Machine repaired successfully.",
        )

        confirm_outcome(outcome)

        self.work_item.refresh_from_db()

        self.assertEqual(
            self.work_item.status,
            WorkItem.Status.IN_PROGRESS,
        )

class OutcomeExecutionAssociationTests(TestCase):

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

        self.employee = User.objects.create_user(
            username="employee",
            email="employee@test.com",
            password="TestPassword123!",
            company=self.company,
            department=self.department,
            role=User.Role.EMPLOYEE,
            first_name="Test",
            last_name="Employee",
        )

        self.work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.employee,
            title="Repair stitching machine",
            planned_at=datetime(
                2026,
                10,
                8,
                8,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
            status=WorkItem.Status.IN_PROGRESS,
        )

        self.execution = WorkExecution.objects.create(
            company=self.company,
            work_item=self.work_item,
            employee=self.employee,
            started_at=datetime(
                2026,
                10,
                8,
                8,
                15,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
            ended_at=datetime(
                2026,
                10,
                8,
                9,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        self.outcome = Outcome.objects.create(
            company=self.company,
            work_item=self.work_item,
            employee=self.employee,
            description="Machine repaired successfully.",
        )

    def test_execution_can_be_attached_to_outcome(self):
        attach_execution_to_outcome(
            outcome=self.outcome,
            execution=self.execution,
        )

        self.assertIn(
            self.execution,
            self.outcome.executions.all(),
        )

    def test_execution_can_be_attached_only_once(self):
        attach_execution_to_outcome(
            outcome=self.outcome,
            execution=self.execution,
        )

        attach_execution_to_outcome(
            outcome=self.outcome,
            execution=self.execution,
        )

        self.assertEqual(
            self.outcome.executions.count(),
            1,
        )

    def test_execution_from_another_company_is_rejected(self):
        other_company = Company.objects.create(
            name="Other Company",
            code="OTHER",
        )

        other_department = Department.objects.create(
            company=other_company,
            name="Operations",
            code="OPS",
        )

        other_employee = User.objects.create_user(
            username="other_employee",
            email="other@test.com",
            password="TestPassword123!",
            company=other_company,
            department=other_department,
            role=User.Role.EMPLOYEE,
        )

        other_work_item = WorkItem.objects.create(
            company=other_company,
            department=other_department,
            owner=other_employee,
            title="Other work",
            planned_at=datetime(
                2026,
                10,
                8,
                8,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        other_execution = WorkExecution.objects.create(
            company=other_company,
            work_item=other_work_item,
            employee=other_employee,
            started_at=datetime(
                2026,
                10,
                8,
                8,
                15,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        with self.assertRaises(ValidationError):
            attach_execution_to_outcome(
                outcome=self.outcome,
                execution=other_execution,
            )

    def test_execution_from_another_work_item_is_rejected(self):
        other_work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.employee,
            title="Prepare production report",
            planned_at=datetime(
                2026,
                10,
                8,
                10,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        other_execution = WorkExecution.objects.create(
            company=self.company,
            work_item=other_work_item,
            employee=self.employee,
            started_at=datetime(
                2026,
                10,
                8,
                10,
                15,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        with self.assertRaises(ValidationError):
            attach_execution_to_outcome(
                outcome=self.outcome,
                execution=other_execution,
            )

    def test_multiple_executions_can_be_attached_to_same_outcome(self):
        second_execution = WorkExecution.objects.create(
            company=self.company,
            work_item=self.work_item,
            employee=self.employee,
            started_at=datetime(
                2026,
                10,
                8,
                14,
                0,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
            ended_at=datetime(
                2026,
                10,
                8,
                14,
                45,
                tzinfo=ZoneInfo("Africa/Nairobi"),
            ),
        )

        attach_execution_to_outcome(
            outcome=self.outcome,
            execution=self.execution,
        )

        attach_execution_to_outcome(
            outcome=self.outcome,
            execution=second_execution,
        )

        self.assertEqual(
            self.outcome.executions.count(),
            2,
        )