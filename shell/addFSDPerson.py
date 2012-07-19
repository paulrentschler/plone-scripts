#!/usr/bin/env python

"""A module which allows for adding FSD people to Plone sites."""

import sys
import ldapLookup
import getpass
from xmlrpclib import ServerProxy


class AddFSDPerson(object):
    host = 'localhost'
    port = '3030'
    fsd = '/huck/people'
    ploneClient = False


    def __init__(self):
        """Processes the command line arguments and stores the values provided.
           """
        if len(sys.argv) > 1 and sys.argv[1] == 'help':
            self._displaySyntax()
            
        elif len(sys.argv) > 1:
            # separate the host, port, and fsd path from the first command line argument
            self.host, self.port = sys.argv[1].strip('http://').split(':')
            self.port, self.fsd = self.port.split('/', 1)
            self.fsd = '/' + self.fsd
            
            # create the connection to the Plone site
            self._connectToPlone()
            
            # check for the other command line arguments
            if len(sys.argv) > 2:
                accessId = sys.argv[2]
                firstName, middleName, lastName = self._getUsernameFromLDAP(accessId)
                if firstName <> '' and lastName <> '':
                    self._createPersonObject(accessId, firstName, lastName, middleName)
                else:
                    print "failed to create a person object with id %s. A first and last name could not be determined." % accessId
                
            if len(sys.argv) > 4:
                id = sys.argv[2]
                firstName = sys.argv[3]
                lastName = sys.argv[4]
                try:
                    middleName = sys.argv[5]
                except IndexError:
                    middleName = ""
                self._createPersonObject(accessId, firstName, lastName, middleName)


    def isConnectedToPlone(self):
        """Returns whether a connection to the Plone site exists.
           """
        if type(self.ploneClient) <> type(False):
            return True
        else:
            return False


    def getPloneSiteInformation(self):
        """Asks the user to provide the host, port, and FSD directory information.
           """
        self.host = self._promptWithDefault("What is the host name for the server (ex: localhost)", self.host)
        self.port = self._promptWithDefault("What port is Zope running on (ex: 8080)", self.port)
        self.fsd = self._promptWithDefault("What is the path to the FSD directory (ex: /plone/people)", self.fsd)
        self._connectToPlone()


    def interactiveAddUsers(self):
        """Guide the user through adding a user to the Plone site by asking
           them a series of questions. Then allow them to add another user.
           """
        while True:
            if self.isConnectedToPlone():
                print "Using the existing connection to http://%s:%s." % (self.host, self.port)
            else:
                self.getPloneSiteInformation()
            
            accessId = raw_input("What is the Access Account ID for the user (ex: abc123)? ")
            firstName, middleName, lastName = self._getUsernameFromLDAP(accessId)
            firstName = self._promptWithDefault("What is the person's first name", firstName)
            middleName = self._promptWithDefault("What is the person's middle names", middleName)
            lastName = self._promptWithDefault("What is the person's last name", lastName)
            
            self._createPersonObject(accessId, firstName, lastName, middleName)
            
            again = raw_input("\nDo you want to add another person (y/n)? ")
            if again.lower() == 'n':
                break
            else:
                accessId = firstName = middleName = lastName = ''
                print "\n"


    def _connectToPlone(self):
        """Establishes a connection to the Plone site.
           """
        user = self._promptWithDefault("Enter the ZMI username to connect as", 'admin')
        pw = getpass.getpass(prompt="Enter the ZMI password: ")
        print pw
        plone, path = self.fsd[1:].split('/', 1)
        connectString = "http://%s:%s@%s:%s%s" % (user, pw, self.host, self.port, '/' + plone)
        try:
            self.ploneClient = ServerProxy(connectString)
            print "Connection established to http://%s:%s%s" % (self.host, self.port, '/' + plone)
        except:
            self.ploneClient = False


    def _getUsernameFromLDAP(self, accessId):
        """Queries the PSU LDAP server to get the user's
           first, middle, and last name.
           """
        firstName = middleName = lastName = ''
        
        ldapClient = ldapLookup.PsuLdap()
        person = ldapClient.member_search(accessId)
        if len(person) > 0:
            lastName = person['sn'][0].capitalize().strip()
            givenName = person['givenName'][0] + ' '
            fName, mName = givenName.split(' ', 1)
            firstName = fName.capitalize().strip()
            middleName = mName.capitalize().strip()
            
        return (firstName, middleName, lastName)


    def _createPersonObject(self, accessId, firstName, lastName, middleName = ''):
        """Creates the person object with the specified parameters.
           """
        if type(self.ploneClient) <> type(False):
           idPath = self.fsd
           if idPath[len(idPath) - 1] != '/':
               idPath += '/'

           idPath += accessId
           personData = { idPath: [{'firstName': firstName, 'middleName': middleName, 'lastName': lastName}, 'FSDPerson'] }

           try:
               personObj = self.ploneClient.get_object(self.ploneClient.post_object(personData))
               print "%s %s person object created with id: %s." % (firstName, lastName, accessId)
           except:
               print "failed to create %s %s with ID: %s." % (firstName, lastName, accessId)


    def _promptWithDefault(self, prompt, value):
        """Prompts the user for a value and provides a default value.
           """
        newValue = raw_input("%s [%s]: " % (prompt, value))
        if newValue == '':
            newValue = value
        elif newValue == ' ':
            newValue = ''
        
        return newValue


    def _displaySyntax(self):
        """
Add people to the Faculty / Staff Directory of a Plone site from the command line.
   syntax: addFSDPerson.py <plone site> <id> <first name> <last name> [<middle name>]

   plone site     the URL and port to the ZMI of the site you want to add to
                    example: http://localhost:8080/plone/people
   id             the Access Account ID for the person
                    example: abc123
   first name     the first name of the person being added
   last name      the last name of the person being added
   middle name    the middle name of the person being added (optional)

           """
        print self._displaySyntax.__doc__



if __name__ == '__main__':
    obj = AddFSDPerson()
    if len(sys.argv) <= 2:
        obj.interactiveAddUsers()

