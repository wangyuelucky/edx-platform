from django.conf import settings
from django.test import TestCase, LiveServerTestCase
# from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from external_auth.views import shib_login
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.base import SessionBase

#Shib is supposed to provide 'REMOTE_USER', 'givenName', 'sn', 'mail', 'Shib-Identity-Provider'
#attributes via request.META.  We can count on 'Shib-Identity-Provider', and 'REMOTE_USER' being present
#b/c of how mod_shib works but should test the behavior with the rest of the attributes present/missing
idp = 'https://idp.stanford.edu/'
REMOTE_USER = 'test_user@stanford.edu'
mails = [None, '', 'test_user@stanford.edu']
givenNames = [None, '', 'Jason', 'jason; John; bob'] # At Stanford, the givenNames can be a list delimited by ';'
sns = [None, '', 'Bau', 'bau; smith'] # At Stanford, the sns can be a list delimited by ';'


class ShibSPTest(TestCase):
    """ 
    Tests for the Shibboleth SP, which communicates via request.META
    (Apache environment variables set by mod_shib)
    """
    factory = RequestFactory()


    def testTrivial(self):
        self.assertEquals(1+1,2)
    
    def __test_looper(self, testfn):
        """ 
        This helps exercise the system by looping over all combinations
        of test inputs.
        """
        for mail in mails:
            for givenName in givenNames:
                for sn in sns:
                    request = self.factory.request()
                    request.method = 'GET'
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
        factory = RequestFactory()
        
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