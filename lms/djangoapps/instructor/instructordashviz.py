# Fetch and format data for the instructor dashboard visualizations
import json
from time import mktime
from itertools import groupby
from django.db.models import Q

from django.contrib.auth.models import User, Group
from track.models import TrackingLog
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

    def enrollment_change(self):
        course_id = self.course_id
        enroll_string   = '{"POST": {"course_id": ["%s"], "enrollment_action": ["enroll"]}, "GET": {}}' % course_id
        unenroll_string = '{"POST": {"course_id": ["%s"], "enrollment_action": ["unenroll"]}, "GET": {}}' % course_id

        tracks = TrackingLog.objects.filter(
            Q(event=enroll_string) | Q(event=unenroll_string),
            event_type='/change_enrollment'
            ).order_by('time')

        def extract_from_trackinglog(tracking_log):
            if tracking_log.event == enroll_string:
                state = 'enroll'
            elif tracking_log.event == unenroll_string:
                state = 'unenroll'
            else:
                state = 'unknown'

            convert_time = lambda time: int(mktime(time.timetuple()))

            return (convert_time(tracking_log.time), state)

        track_events = map(extract_from_trackinglog, tracks)
        track_events_numbered = [[time_int, {'enroll': 1, 'unenroll': -1}[state]] for [time_int, state] in track_events]

        # total enrollment (as calculated from starting at 0 and counting changes) at a given time
        integral = []
        enrollment = 0
        for [time_int, increment] in track_events_numbered:
            enrollment += increment
            integral.append([time_int, enrollment])

        output = {}
        output['track_events'] = track_events
        output['track_events_numbered'] = track_events_numbered
        output['data'] = integral
        return json.dumps(output)

# def index_without_error(list, item):
#     try:
#         return list.index(item)
#     except ValueError:
#         return Infinity
