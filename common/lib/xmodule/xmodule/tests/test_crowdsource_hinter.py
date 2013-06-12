from mock import Mock, patch
import unittest

import xmodule
from xmodule.crowdsource_hinter import CrowdsourceHinterModule
from xmodule.modulestore import Location

from django.http import QueryDict

from . import test_system

import json

class CHModuleFactory(object):
    '''
    Helps us make a CrowdsourceHinterModule with the specified internal
    state.
    '''

    sample_problem_xml = '''
    <?xml version="1.0"?>
    <crowdsource_hinter>
        <problem display_name="Numerical Input" markdown="A numerical input problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.&#10;&#10;The answer is correct if it is within a specified numerical tolerance of the expected answer.&#10;&#10;Enter the number of fingers on a human hand:&#10;= 5&#10;&#10;[explanation]&#10;If you look at your hand, you can count that you have five fingers. [explanation] " rerandomize="never" showanswer="finished">
          <p>A numerical input problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.</p>
          <p>The answer is correct if it is within a specified numerical tolerance of the expected answer.</p>
          <p>Enter the number of fingers on a human hand:</p>
          <numericalresponse answer="5">
            <textline/>
          </numericalresponse>
          <solution>
            <div class="detailed-solution">
              <p>Explanation</p>
              <p>If you look at your hand, you can count that you have five fingers. </p>
            </div>
          </solution>
        </problem>
    </crowdsource_hinter>
    '''

    num = 0

    @staticmethod
    def next_num():
        CHModuleFactory.num += 1
        return CHModuleFactory.num

    @staticmethod
    def create(hints=None,
               previous_answers=None,
               user_voted=None):

        location = Location(["i4x", "edX", "capa_test", "problem",
                             "SampleProblem{0}".format(CHModuleFactory.next_num())])
        model_data = {'data': CHModuleFactory.sample_problem_xml}

        if hints != None:
            model_data['hints'] = hints
        if previous_answers != None:
            model_data['previous_answers'] = previous_answers
        if user_voted != None:
            model_data['user_voted'] = user_voted
        
        descriptor = Mock(weight="1")
        system = test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CrowdsourceHinterModule(system, location, descriptor, model_data)
        return module

class CrowdsourceHinterTest(unittest.TestCase):

    def test_gethint_0hint(self):
        '''
        Someone asks for a hint, when there's no hint to give.
        Output should be blank.
        '''
        m = CHModuleFactory.create(hints = {
                'ans1': [['A hint', 9000]],
            })
        json_in = {'problem_name': ['wrong answer']}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue(json_out == ' ')
        print m.previous_answers

    def test_gethint_1hint(self):
        '''
        Someone asks for a hint, with exactly one hint in the database.
        Output should contain that hint.
        '''
        m = CHModuleFactory.create(hints={
                'wrong answer': [['This is a hint', 42]],
                'ans1': [['A hint', 9000]],
            })
        json_in = {'problem_name': ['wrong answer']}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('This is a hint' in json_out)


    def test_gethint_manyhints(self):
        '''
        Someone asks for a hint, with many matching hints in the database.
        - The top-rated hint should be returned.
        - Two other random hints should be returned.
        Currently, the best hint could be returned twice - need to fix this
        in implementation.
        '''
        m = CHModuleFactory.create(hints={
                'wrong answer': [['Best hint', 9000],
                                 ['another hint', 10],
                                 ['another hint', 9],
                                 ['yet another hint', 8]],
            })
        json_in = {'problem_name': ['wrong answer']}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('Best hint' in json_out)
        self.assertTrue(json_out.count('another hint') >= 1)

    def test_getfeedback_0wronganswers(self):
        '''
        Someone has gotten the problem correct on the first try.
        Output should be empty.
        '''
        m = CHModuleFactory.create()
        json_in = {'problem_name': ['right answer']}
        json_out = json.loads(m.get_feedback(json_in))['contents']
        self.assertTrue(json_out == ' ')

    def test_getfeedback_1wronganswer_nohints(self):
        '''
        Someone has gotten the problem correct, with one previous wrong
        answer.  However, we don't actually have hints for this problem.
        There should be a dialog to submit a new hint.
        '''
        m = CHModuleFactory.create(hints={},
            previous_answers=[
                ['wrong answer', [None, None, None]]],
            )
        json_in = {'problem_name': ['right answer']}
        json_out = json.loads(m.get_feedback(json_in))['contents']
        self.assertTrue('textarea' in json_out)
        self.assertTrue('Vote' not in json_out)


    def test_getfeedback_1wronganswer_withhints(self):
        '''
        Same as above, except the user did see hints.  There should be
        a voting dialog, with the correct choices, plus a hint submission
        dialog.
        '''
        m = CHModuleFactory.create(hints={
                'wrong answer': [['a hint', 42],
                                 ['another hint', 35],
                                 ['irrelevent hint', 25]]
            },
            previous_answers=[
                ['wrong answer', [0, 1, None]]],
            )
        json_in = {'problem_name': ['right answer']}
        json_out = json.loads(m.get_feedback(json_in))['contents']
        self.assertTrue('a hint' in json_out)
        self.assertTrue('another hint' in json_out)
        self.assertTrue('irrelevent hint' not in json_out)
        self.assertTrue('textarea' in json_out)


    def test_vote_nopermission(self):
        '''
        A user tries to vote for a hint, but he has already voted!
        Should not change any vote tallies.
        '''
        m = CHModuleFactory.create(hints={
                'wrong answer': [['a hint', 42],
                                 ['another hint', 35],
                                 ['irrelevent hint', 25]]
            },
            previous_answers=[
                ['wrong answer', [0, 1, None]]],
            user_voted=True
            )
        json_in = {'answer': 0, 'hint': 1}
        json_out = json.loads(m.tally_vote(json_in))['contents']
        self.assertTrue(m.hints['wrong answer'][0][1] == 42)
        self.assertTrue(m.hints['wrong answer'][1][1] == 35)
        self.assertTrue(m.hints['wrong answer'][2][1] == 25)


    def test_vote_withpermission(self):
        '''
        A user votes for a hint.
        '''
        m = CHModuleFactory.create(hints={
                'wrong answer': [['a hint', 42],
                                 ['another hint', 35],
                                 ['irrelevent hint', 25]]
            },
            previous_answers=[
                ['wrong answer', [0, 1, None]]],
            )
        json_in = {'answer': 0, 'hint': 1}
        json_out = json.loads(m.tally_vote(json_in))['contents'] 
        self.assertTrue(m.hints['wrong answer'][0][1] == 42)
        self.assertTrue(m.hints['wrong answer'][1][1] == 36)
        self.assertTrue(m.hints['wrong answer'][2][1] == 25)


    def test_submithint_nopermission(self):
        '''
        A user tries to submit a hint, but he has already voted.
        '''
        m = CHModuleFactory.create(previous_answers=[
                ['wrong answer', [None, None, None]]],
            user_voted=True)
        json_in = {'answer': 0, 'hint': 'This is a new hint.'}
        m.submit_hint(json_in)
        self.assertTrue('wrong answer' not in m.hints)


    def test_submithint_withpermission_new(self):
        '''
        A user submits a hint to an answer for which no hints
        exist yet.
        '''
        m = CHModuleFactory.create(previous_answers=[
                ['wrong answer', [None, None, None]]],
            )
        json_in = {'answer': 0, 'hint': 'This is a new hint.'}
        m.submit_hint(json_in)
        # Make a hint request.
        json_in = {'problem name': ['wrong answer']}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('This is a new hint.' in json_out)


    def test_submithint_withpermission_existing(self):
        '''
        A user submits a hint to an answer that has other hints
        already.
        '''
        m = CHModuleFactory.create(previous_answers=[
                ['wrong answer', [0, None, None]]],
            hints={'wrong answer': [['Existing hint.', 1]]},
        )
        json_in = {'answer': 0, 'hint': 'This is a new hint.'}
        m.submit_hint(json_in)
        # Make a hint request.
        json_in = {'problem name': ['wrong answer']}
        json_out = json.loads(m.get_hint(json_in))['contents']
        self.assertTrue('This is a new hint.' in json_out)













