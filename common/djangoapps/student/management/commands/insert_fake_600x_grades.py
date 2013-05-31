from optparse import make_option
import json
from datetime import datetime

from django.core.management.base import BaseCommand, CommandError

from django.contrib.auth.models import User
from student.models import UserProfile, CourseEnrollment


class Command(BaseCommand):

    args = '<>'
    help = """
    Add fake students and grades to db.
    """

    # option_list = BaseCommand.option_list + (
    #     make_option('--course_id',
    #                 action='store',
    #                 dest='course_id',
    #                 help='Specify a particular course.'),
    #     make_option('--exam_series_code',
    #                 action='store',
    #                 dest='exam_series_code',
    #                 default=None,
    #                 help='Specify a particular exam, using the Pearson code'),
    #     make_option('--accommodation_pending',
    #                 action='store_true',
    #                 dest='accommodation_pending',
    #                 default=False,
    #                 ),
    # )

    def handle(self, *args, **options):
        print "hello"

        seed_num = 5
        email = 'jd%s@edx.org' % seed_num
        User.objects.create_user(username='johndoe%s' % seed_num, email='jd%s@edx.org' % seed_num, password='1234')
        y = UserProfile(user=User.objects.filter(email='jd%s@edx.org' % seed_num)[0], name='John Doe 3')
        y.save()
        # z = CourseEnrollment()
        # z.save()
