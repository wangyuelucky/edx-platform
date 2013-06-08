from django.conf import settings
from django.test import TestCase, LiveServerTestCase
# from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from external_auth.views import shib_login, course_specific_login, course_specific_register
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase
from django.test.utils import override_settings
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.inheritance import own_metadata
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore

#Shib is supposed to provide 'REMOTE_USER', 'givenName', 'sn', 'mail', 'Shib-Identity-Provider'
#attributes via request.META.  We can count on 'Shib-Identity-Provider', and 'REMOTE_USER' being present
#b/c of how mod_shib works but should test the behavior with the rest of the attributes present/missing
idp = 'https://idp.stanford.edu/'
REMOTE_USER = 'test_user@stanford.edu'
mails = [None, '', 'test_user@stanford.edu']
givenNames = [None, '', 'Jason', 'jason; John; bob'] # At Stanford, the givenNames can be a list delimited by ';'
sns = [None, '', 'Bau', 'bau; smith'] # At Stanford, the sns can be a list delimited by ';'

@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class ShibSPTest(ModuleStoreTestCase):
    """ 
    Tests for the Shibboleth SP, which communicates via request.META
    (Apache environment variables set by mod_shib)
    """
    factory = RequestFactory()
    
    def __test_looper(self, testfn):
        """ 
        This helps exercise the system by looping over all combinations
        of test inputs.
        """
        for mail in mails:
            for givenName in givenNames:
                for sn in sns:
                    request = self.factory.get('/shib-login')
                    request.META.update({'Shib-Identity-Provider': idp,
                                        'REMOTE_USER': REMOTE_USER})
                    if mail is not None:
                        request.META.update({'mail': mail})
                    if givenName is not None:
                        request.META.update({'givenName': givenName})
                    if sn is not None:
                        request.META.update({'sn': sn})                    
                    testfn(request, mail, givenName, sn)

    def testRegistrationForm(self):
        """
        Tests the registration form popping up with the proper parameters.
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        def _test_helper(request, mail, givenName, sn):
            request.user = AnonymousUser() #user must not be logged in
            request.session = SessionBase() #empty session
            
            response = shib_login(request)
            self.assertEquals(response.status_code, 200)
            mail_input_HTML =  '<input class="" id="email" type="email" name="email"'
            if not mail:
                self.assertContains(response, mail_input_HTML)
            else:
                self.assertNotContains(response, mail_input_HTML)
            sn_empty = (sn is None) or (sn.strip() == '')
            givenName_empty = (givenName is None) or (givenName.strip() == '')
            fullname_input_HTML = '<input id="name" type="text" name="name"'
            if sn_empty and givenName_empty:
                self.assertContains(response, fullname_input_HTML)
            else:
                self.assertNotContains(response, fullname_input_HTML)
        
            #clean up b/c we don't want existing ExternalAuthMap for the next run
            request.session['ExternalAuthMap'].delete() 


        self.__test_looper(_test_helper)

    def testRegistrationFormSubmit(self):
        """
        Tests user creation after the registration form that pops is submitted
        """
        pass


    def testCourseSpecificLoginAndReg(self):
        """
        Tests that the correct course specific login and registration urls work for shib
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        ## Need to modify course metadata, so try to go through the store
        try:
            store = modulestore('direct')
        except KeyError:
            store = modulestore()

    
        # Test for cases where course if found
        for domain in ["", "shib:https://idp.stanford.edu/"]:
            #set domains
            course.enrollment_domain = domain
            metadata = own_metadata(course)
            metadata['enrollment_domain'] = domain
            store.update_metadata(course.location.url(), metadata)

            #setting location to test that GET params get passed through
            login_request = self.factory.get('/course_specific_login/MITx/999/Robot_Super_Course' +
                                                 '?course_id=MITx/999/Robot_Super_Course' +
                                                 '&enrollment_action=enroll')
            reg_request = self.factory.get('/course_specific_register/MITx/999/Robot_Super_Course' +
                                               '?course_id=MITx/999/course/Robot_Super_Course' +
                                               '&enrollment_action=enroll')

            login_response = course_specific_login(login_request, 'MITx/999/Robot_Super_Course')
            reg_response = course_specific_register(login_request, 'MITx/999/Robot_Super_Course')

            if "shib" in domain:
                self.assertTrue(isinstance(login_response, HttpResponseRedirect))
                self.assertEqual(login_response['Location'], reverse('shib-login') +
                                                       '?course_id=MITx/999/Robot_Super_Course' +
                                                       '&enrollment_action=enroll')
                self.assertTrue(isinstance(login_response, HttpResponseRedirect))
                self.assertEqual(reg_response['Location'], reverse('shib-login') +
                                                       '?course_id=MITx/999/Robot_Super_Course' +
                                                       '&enrollment_action=enroll')
            else:
                self.assertTrue(isinstance(login_response, HttpResponseRedirect))
                self.assertEqual(login_response['Location'], reverse('signin_user') +
                                                       '?course_id=MITx/999/Robot_Super_Course' +
                                                       '&enrollment_action=enroll')
                self.assertTrue(isinstance(login_response, HttpResponseRedirect))
                self.assertEqual(reg_response['Location'], reverse('register_user') +
                                                       '?course_id=MITx/999/Robot_Super_Course' +
                                                       '&enrollment_action=enroll')


            # Now test for non-existent course
            #setting location to test that GET params get passed through
            login_request = self.factory.get('/course_specific_login/DNE/DNE/DNE' +
                                             '?course_id=DNE/DNE/DNE' +
                                             '&enrollment_action=enroll')
            reg_request = self.factory.get('/course_specific_register/DNE/DNE/DNE' +
                                           '?course_id=DNE/DNE/DNE/Robot_Super_Course' +
                                           '&enrollment_action=enroll')
                    
            login_response = course_specific_login(login_request, 'DNE/DNE/DNE')
            reg_response = course_specific_register(login_request, 'DNE/DNE/DNE')

            self.assertTrue(isinstance(login_response, HttpResponseRedirect))
            self.assertEqual(login_response['Location'], reverse('signin_user') +
                                                         '?course_id=DNE/DNE/DNE' +
                                                         '&enrollment_action=enroll')
            self.assertTrue(isinstance(login_response, HttpResponseRedirect))
            self.assertEqual(reg_response['Location'], reverse('register_user') +
                                                         '?course_id=DNE/DNE/DNE' +
                                                         '&enrollment_action=enroll')




