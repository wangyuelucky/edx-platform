"""
Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the mitx dir
2. django-admin.py schemamigration student --auto --settings=lms.envs.dev --pythonpath=. description_of_your_change
3. Add the migration file created in mitx/common/djangoapps/student/migrations/
"""

# TODO move CourseGradesCache here.
