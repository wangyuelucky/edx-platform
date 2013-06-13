"""
Unit tests for LMS instructor-initiated background tasks, 

Runs tasks on answers to course problems to validate that code
paths actually work.

"""
import logging
import json
from uuid import uuid4

from mock import Mock, patch
import textwrap

from celery.states import SUCCESS, FAILURE
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from capa.tests.response_xml_factory import (CodeResponseXMLFactory,
                                             CustomResponseXMLFactory)
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware.model_data import StudentModule
from courseware.tests.factories import StudentModuleFactory
from student.tests.factories import UserFactory

from instructor_task.models import InstructorTask
from instructor_task.tests.test_base import InstructorTaskTestCase, TEST_COURSE_ORG, TEST_COURSE_NUMBER
from instructor_task.tests.factories import InstructorTaskFactory
from instructor_task.tasks import reset_problem_attempts
from instructor_task.tasks_helper import UpdateProblemModuleStateError

log = logging.getLogger(__name__)
PROBLEM_URL_NAME = "test_urlname"


class TestInstructorTasks(InstructorTaskTestCase):
    def setUp(self):
        self.initialize_course()
        self.instructor = self.create_instructor('instructor')
        self.problem_url = InstructorTaskTestCase.problem_location(PROBLEM_URL_NAME)

    def _create_input_entry(self, student=None):
        """Creates a InstructorTask entry for testing."""
        task_id = str(uuid4())
        task_input = {'problem_url': self.problem_url}
        if student is not None:
            task_input['student'] = student.username

        instructor_task = InstructorTaskFactory.create(course_id=self.course.id,
                                                       requester=self.instructor,
                                                       task_input=json.dumps(task_input),
                                                       task_key='dummy value',
                                                       task_id=task_id)
        return instructor_task

    def _get_xmodule_instance_args(self):
        """
        Calculate dummy values for parameters needed for instantiating xmodule instances.
        """
        return {'xqueue_callback_url_prefix': 'dummy_value',
                'request_info': {},
                }

    def _run_task_with_mock_celery(self, task_class, entry_id, task_id):
        mock_task = Mock()
        mock_task.request = Mock()
        mock_task.request.id = task_id
        with patch('instructor_task.tasks_helper._get_current_task') as mock_get_task:
            mock_get_task.return_value = mock_task
            return task_class(entry_id, self._get_xmodule_instance_args())

    def test_missing_current_task(self):
        # run without (mock) Celery running
        task_entry = self._create_input_entry()
        with self.assertRaises(UpdateProblemModuleStateError):
            reset_problem_attempts(task_entry.id, self._get_xmodule_instance_args())

    def test_undefined_problem(self):
        # run with celery, but no problem defined
        task_entry = self._create_input_entry()
        with self.assertRaises(ItemNotFoundError):
            self._run_task_with_mock_celery(reset_problem_attempts, task_entry.id, task_entry.task_id)

    def _assert_return_matches_entry(self, returned, entry_id):
        entry = InstructorTask.objects.get(id=entry_id)
        self.assertEquals(returned, json.loads(entry.task_output))

    def test_run_with_no_state(self):
        # run with no StudentModules for the problem
        task_entry = self._create_input_entry()
        self.define_option_problem(PROBLEM_URL_NAME)
        status = self._run_task_with_mock_celery(reset_problem_attempts, task_entry.id, task_entry.task_id)
        # check return value
        self.assertTrue('duration_ms' in status)
        self.assertEquals(status.get('attempted'), 0)
        self.assertEquals(status.get('updated'), 0)
        self.assertEquals(status.get('total'), 0)
        self.assertEquals(status.get('action_name'), 'reset')
        # compare with entry in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        self.assertEquals(json.loads(entry.task_output), status)
        self.assertEquals(entry.task_state, SUCCESS)

    def test_run_with_some_state(self):
        # run with some StudentModules for the problem
        task_entry = self._create_input_entry()
        self.define_option_problem(PROBLEM_URL_NAME)
        num_students = 10
        students = [
            UserFactory.create(username='robot%d' % i, email='robot+test+%d@edx.org' % i)
            for i in xrange(num_students)
        ]
        for student in students:
            StudentModuleFactory.create(course_id=self.course.id, module_state_key=self.problem_url, student=student)

        status = self._run_task_with_mock_celery(reset_problem_attempts, task_entry.id, task_entry.task_id)
        # check return value
        self.assertTrue('duration_ms' in status)
        self.assertEquals(status.get('attempted'), num_students)
        self.assertEquals(status.get('updated'), num_students)
        self.assertEquals(status.get('total'), num_students)
        self.assertEquals(status.get('action_name'), 'reset')
        # compare with entry in table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        self.assertEquals(json.loads(entry.task_output), status)
        self.assertEquals(entry.task_state, SUCCESS)
        # TODO: check that entries were reset
