from django.conf import settings
from django.test import TestCase, LiveServerTestCase
# from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory, Client
from external_auth.views import shib_login, course_specific_login, course_specific_register
from django.contrib.auth.models import AnonymousUser, User
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
from student.tests.factories import UserFactory
from external_auth.models import ExternalAuthMap
from student.views import create_account, change_enrollment
from student.models import UserProfile, Registration, CourseEnrollment

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
    
    # Putting this in setUp instead of __init__ due to interactions with @override_settings that
    # I don't want to debug right now
    def setUp(self):
        try:
            self.store = modulestore('direct')
        except KeyError:
            self.store = modulestore()

    def __test_looper(self, testfn):
        """
        This helps exercise the system by looping over all combinations
        of test inputs.
        """
        for mail in mails:
            for givenName in givenNames:
                for sn in sns:
                    meta_dict = {}
                    meta_dict.update({'Shib-Identity-Provider': idp,
                                        'REMOTE_USER': REMOTE_USER})
                    if mail is not None:
                        meta_dict.update({'mail': mail})
                    if givenName is not None:
                        meta_dict.update({'givenName': givenName})
                    if sn is not None:
                        meta_dict.update({'sn': sn})
                    testfn(meta_dict, mail, givenName, sn)
    

    
    def testShibLogin(self):
        """
        Tests that a user with a shib ExternalAuthMap gets logged in while when
        shib-login is called, while a user without such gets the registration form.
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        student = UserFactory.create()
        extauth = ExternalAuthMap(external_id='testuser@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  user=student)
        student.save()
        extauth.save()

        idps = ['https://idp.stanford.edu/', 'https://someother.idp.com/']
        REMOTE_USERS = ['testuser@stanford.edu', 'testuser2@someother_idp.com']
        
        for idp in idps:
            for REMOTE_USER in REMOTE_USERS:
                request = self.factory.get('/shib-login')
                request.session = SessionBase() #empty session
                request.META.update({'Shib-Identity-Provider': idp,
                                      'REMOTE_USER': REMOTE_USER})
                request.user = AnonymousUser()
                response = shib_login(request)
                if idp is "https://idp.stanford.edu" and REMOTE_USER is 'testuser@stanford.edu':
                    self.assertTrue(isinstance(response, HttpResponseRedirect))
                    self.assertEqual(request.user, student)
                    self.assertEqual(response['Location'], '/')
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "<title>Register for")

    def testRegistrationForm(self):
        """
        Tests the registration form showing up with the proper parameters.
            
        Uses django test client for its session support
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return
        
        def _test_helper(meta_dict, mail, givenName, sn):
            self.client.logout()
            request_kwargs = {'path': '/shib-login/', 'data': {}, 'follow': False}
            request_kwargs.update(meta_dict)
            response = self.client.get(**request_kwargs)
            
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
            self.client.session['ExternalAuthMap'].delete()


        self.__test_looper(_test_helper)

    def testRegistrationFormSubmit(self):
        """
        Tests user creation after the registration form that pops is submitted.  If there is no shib
        ExternalAuthMap in the session, then the created user should take the username and email from the
        request.
            
        Uses django test client for its session support
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        
        def _test_helper(meta_dict, mail, givenName, sn):
            #First we pop the registration form
            self.client.logout()
            request1_kwargs = {'path': '/shib-login/', 'data': {}, 'follow': False}
            request1_kwargs.update(meta_dict)
            response1 = self.client.get(**request1_kwargs)
            #Then we have the user answer the registration form
            request2 = self.factory.post('/create_account')
            postvars = {'email': 'post_email@stanford.edu',
                        'username': 'post_username',
                        'password': 'post_password',
                        'name': 'post_name',
                        'terms_of_service': 'true',
                        'honor_code': 'true'}
            request2_kwargs = {'path': '/create_account', 'data': postvars, 'follow': False}
            response2 = self.client.post(**request2_kwargs)
                            
            #check that the created user has the right email, either taken from shib or user input
            if mail:
                self.assertEqual(list(User.objects.filter(email=postvars['email'])), [])
                user = User.objects.get(email=mail)
                self.assertIsNotNone(user)
            else:
                self.assertEqual(list(User.objects.filter(email=mail)), [])
                user = User.objects.get(email=postvars['email'])
                self.assertIsNotNone(user)
                
            #check that the created user profile has the right name, either taken from shib or user input
            profile = UserProfile.objects.get(user=user)
                    
            sn_empty = (sn is None) or (sn.strip() == '')
            givenName_empty = (givenName is None) or (givenName.strip() == '')

            if sn_empty and givenName_empty:
                self.assertEqual(profile.name, postvars['name'])
            else:
                self.assertEqual(profile.name, self.client.session['ExternalAuthMap'].external_name)
                    
            #clean up for next loop
            self.client.session['ExternalAuthMap'].delete()
            UserProfile.objects.filter(user=user).delete()
            Registration.objects.filter(user=user).delete()
            user.delete()

        self.__test_looper(_test_helper)


    def testCourseSpecificLoginAndReg(self):
        """
        Tests that the correct course specific login and registration urls work for shib
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        course = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')

    
        # Test for cases where course is found
        for domain in ["", "shib:https://idp.stanford.edu/"]:
            #set domains
            course.enrollment_domain = domain
            metadata = own_metadata(course)
            metadata['enrollment_domain'] = domain
            self.store.update_metadata(course.location.url(), metadata)

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


    def testEnrollmentLimitByDomain(self):
        """ 
            Tests that the enrollmentDomain setting is properly limiting enrollment to those who have
            the proper external auth
        """
    
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        #create 2 course, one with limited enrollment one without
        course1 = CourseFactory.create(org='Stanford', number='123', display_name='Shib Only')
        course1.enrollment_domain = 'shib:https://idp.stanford.edu/'
        metadata = own_metadata(course1)
        metadata['enrollment_domain'] = course1.enrollment_domain
        self.store.update_metadata(course1.location.url(), metadata)
        
        course2 = CourseFactory.create(org='MITx', number='999', display_name='Robot Super Course')
        course2.enrollment_domain = ''
        metadata = own_metadata(course2)
        metadata['enrollment_domain'] = course2.enrollment_domain
        self.store.update_metadata(course2.location.url(), metadata)

    
        # create 3 kinds of students, external_auth matching course1, external_auth not matching, no external auth
        student1 = UserFactory.create()
        student1.save()
        extauth = ExternalAuthMap(external_id='testuser@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  user=student1)
        extauth.save()
        
        student2 = UserFactory.create()
        student2.username = "teststudent2"
        student2.email = "teststudent2@other.edu"
        student2.save()
        extauth = ExternalAuthMap(external_id='testuser1@other.edu',
                                  external_email='',
                                  external_domain='shib:https://other.edu/',
                                  external_credentials="",
                                  user=student2)
        extauth.save()
                
        student3 = UserFactory.create()
        student3.username = "teststudent3"
        student3.email = "teststudent3@gmail.com"
        student3.save()


        #Tests the two case for courses, limited and not
        for course in [course1, course2]:
            for student in [student1, student2, student3]:
                request = self.factory.post('/change_enrollment')
                request.POST.update({'enrollment_action': 'enroll',
                                     'course_id': course.id})
                request.user = student
                response = change_enrollment(request)
                #if course is not limited or student has correct shib extauth then enrollment should be allowed
                if course is course2 or student is student1:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 1)
                    #clean up
                    CourseEnrollment.objects.filter(user=student, course_id=course.id).delete()
                else:
                    self.assertEqual(response.status_code, 400)
                    self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 0)


    def testShibLoginEnrollment(self):
        """ 
            A functionality test that a student with an existing shib login can auto-enroll in a class with GET params
        """
        if not settings.MITX_FEATURES.get('AUTH_USE_SHIB'):
            return

        student = UserFactory.create()
        extauth = ExternalAuthMap(external_id='testuser@stanford.edu',
                                  external_email='',
                                  external_domain='shib:https://idp.stanford.edu/',
                                  external_credentials="",
                                  internal_password="password",
                                  user=student)
        student.set_password("password")
        student.save()
        extauth.save()


        course = CourseFactory.create(org='Stanford', number='123', display_name='Shib Only')
        course.enrollment_domain = 'shib:https://idp.stanford.edu/'
        metadata = own_metadata(course)
        metadata['enrollment_domain'] = course.enrollment_domain
        self.store.update_metadata(course.location.url(), metadata)

        #use django test client for sessions and url processing
        #no enrollment before trying
        self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 0)
        self.client.logout()
        request_kwargs = {'path': '/shib-login/',
                          'data': {'enrollment_action':'enroll', 'course_id':course.id},
                          'follow': False,
                          'REMOTE_USER': 'testuser@stanford.edu',
                          'Shib-Identity-Provider': 'https://idp.stanford.edu/'}
        response = self.client.get(**request_kwargs)
        #successful login is a redirect to "/"
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 'http://testserver/')
        #now there is enrollment
        self.assertEqual(CourseEnrollment.objects.filter(user=student, course_id=course.id).count(), 1)



