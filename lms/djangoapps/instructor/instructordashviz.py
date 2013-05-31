# Fetch and format data for the instructor dashboard visualizations
import json
from itertools import groupby

from django.contrib.auth.models import User, Group
import courseware.grades as grades
from courseware.courses import get_course_by_id

# one instance per request
# gathers data and formats it for the javascript graphs consumption
class InstructorDashViz(object):
    def __init__(self, course_id, request=None):
        self.course_id = course_id
        self.request = request

    def dummy_numbers(self):
        return [50, 40, 50, 50, 60, 40]

    def letter_buckets(self):
        enrolled_students = User.objects.filter(courseenrollment__course_id=self.course_id).prefetch_related("groups").order_by('username')
        course_descriptor = get_course_by_id(self.course_id)
        ascending_grades = sorted(course_descriptor.grade_cutoffs, key=lambda x: course_descriptor.grade_cutoffs[x], reverse=False)
        # TODO is it fair to assume that grades that fall of the bottom of the spectrum be called 'F'?
        ascending_grades = ['F'] + ascending_grades

        def group_list(list):
            d = {}
            for item in list:
                d[item] = d.get(item, 0) + 1
            return d

        def format_dict_by_key_order(d, key_order):
            return sorted(d.items(), key=lambda item: key_order.index(item[0]))

        if len(enrolled_students) > 0:
            grade_objs = [grades.grade(student, self.request, course=course_descriptor) for student in enrolled_students]
            student_letters = [grade_obj['grade'] for grade_obj in grade_objs]
            student_letters = map(lambda l: l if l in ascending_grades else 'F', student_letters)
            letter_buckets = format_dict_by_key_order(group_list(student_letters), ascending_grades)

            output = {}
            output['data'] = [[ascending_grades.index(letter), number] for [letter, number] in letter_buckets]
            output['ascending_grades'] = ascending_grades
            output['debug'] = letter_buckets

            return json.dumps(output)
        else:
            return json.dumps(None)


# def index_without_error(list, item):
#     try:
#         return list.index(item)
#     except ValueError:
#         return Infinity
