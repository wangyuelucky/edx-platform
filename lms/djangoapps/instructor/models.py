"""
Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the mitx dir
2. django-admin.py schemamigration student --auto --settings=lms.envs.dev --pythonpath=. description_of_your_change
3. Add the migration file created in mitx/common/djangoapps/student/migrations/
"""

from django.db import models

import datetime
import json
from django.contrib.auth.models import User, Group
from courseware.courses import get_course_by_id
import courseware.grades as grades


class CourseGradesCache(models.Model):
    """
    Store a cache student grades for a course for fast access from the instructor dashboard
    """

    course_id = models.CharField(max_length=255, unique=True, db_index=True)
    # state contains cached grade data in a json blob
    state = models.TextField(null=True, blank=True)
    outdated = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)
    last_updated = models.DateTimeField(auto_now=False, null=True, blank=True, db_index=True)

    def get_updated(self, request):
        if self.outdated:
            self.update(request)
            return self
        else:
            return self

    # TODO get rid of request parameter
    def update(self, request):
        enrolled_students = User.objects.filter(courseenrollment__course_id=self.course_id).order_by('username')
        course_descriptor = get_course_by_id(self.course_id)
        grade_objs = [grades.grade(student, request, course=course_descriptor) for student in enrolled_students]

        state = {}
        state['student_grades'] = grade_objs
        self.state = json.dumps(state)
        self.outdated = False
        self.last_updated = datetime.datetime.now()
        self.save()
