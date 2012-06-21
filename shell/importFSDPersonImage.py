#!/usr/bin/env python

"""A module which allows for importing images for FSD people in a Plone site.

   TODO:
     - python package for parsing command line parameters?
     - prompt for deleting files after successful upload
     - test with multiple files
     DONE - delete files after successful upload
     - better output for logging purposes
   """

import sys
import os
from xmlrpclib import ServerProxy
from xmlrpclib import Binary


class AddFSDPhoto(object):
    host = 'localhost'
    port = '8080'
    fsd = '/huck/people'
    imageDirectory = '/Users/par117lsb/import'
    user = 'admin'
    ploneClient = False


    def __init__(self):
        """Processes the command line arguments and stores the values provided.
           """
        if len(sys.argv) > 1 and sys.argv[1] == 'help':
            self.displaySyntax()
            
        elif len(sys.argv) == 4:
            # separate the host, port, and fsd path from the first command line argument
            self.host, self.port = sys.argv[1].strip('http://').split(':')
            self.port, self.fsd = self.port.split('/', 1)
            self.fsd = '/' + self.fsd
            
            # store the image directory
            self.imageDirectory = sys.argv[2]
            
            # store the username
            self.user = sys.argv[3]
            
            # grab the password if provided
            try:
                password = sys.argv[4]
            except:
                password = False
            
        else:
            # prompt for the host, port, fsd path, user, and images directory
            self.getParameters()
            password = False
            
        # create the connection to the Plone site
        if self.connectToPlone(password):
            # process the directory of images
            self.importImages()
            
        print "\nImage import complete.\n\n"



    def connectToPlone(self, password):
        """Connect to the specified plone site with the provided credentials
           and set the client reference.
           """
        if password == False:
            password = raw_input("Enter the ZMI password for %s: " % (self.user))
            
        ploneSite, path = self.fsd[1:].split('/', 1)
        connectString = "http://%s:%s@%s:%s/%s" % (self.user, password, self.host, self.port, ploneSite)
        try:
            self.ploneClient = ServerProxy(connectString)
            return True
        except:
            return False


    def displaySyntax(self):
        """
Import image files of people into the Faculty / Staff Directory of a Plone site
from the command line. Image files must be named with the ID of the FSDPerson
object in the Plone site.
    syntax: importFSDPersonImage.py <FSD url> <directory> <username> <password>

    FSD url       the URL, port, and path to the FSD directory you want to 
                   work with
                     example: http://localhost:8080/plone/people
    directory      the directory that contains the images to process/import
    username       the zope level user to log in as
    password       the password for the zope level user (optional)

        """
        print self.displaySyntax.__doc__


    def getFullPath(self, filename):
        """Generates the full path and filename for the given filename using
           the imageDirectory property.
           """
        path = self.imageDirectory
        if path[0:-1] != "/":
            path += "/"
            
        return path + filename


    def getParameters(self):
        """Asks the user to provide the host, port, FSD directory information,
           username, and image directory.
           """
        self.imageDirectory = self.promptWithDefault(
            "Enter the path to the directory with the images (ex: /home/user/images)",
            self.imageDirectory)
        self.host = self.promptWithDefault(
            "What is the host name for the server (ex: localhost)", self.host)
        self.port = self.promptWithDefault(
            "What port is Zope running on (ex: 8080)", self.port)
        self.fsd = self.promptWithDefault(
            "What is the path to the FSD directory (ex: /plone/people)", self.fsd)
        self.user = self.promptWithDefault(
            "Enter the ZMI username to connect as", self.user)


    def importImages(self):
        """Processes the image directory and imports any images into the
           Faculty/Staff Directory of the Plone site
           """
        # verify that the image directory exists
        if os.path.exists(self.imageDirectory):
            for filename in os.listdir(self.imageDirectory):
                digitalId, extention = filename.rsplit('.', 1)
                personPath = "%s/%s" % (self.fsd, digitalId)
                try:
                    image = open(self.getFullPath(filename))
                    personData = { self.fsd + "/" + digitalId: [
                        { 'image': Binary(image.read()) },
                        'FSDPerson',
                    ]}
                except IOError:
                    pass    #no image
                
                # get the current FSD person object
                try:
                    personObj = self.ploneClient.get_object([personPath])
                    
                    # update the FSD person's image
                    try:
                        self.ploneClient.put_object(personData)
                        os.remove(self.getFullPath(filename))
                    except:
                        print "Failed to upload image (%s)\n" % filename
                    
                except:
                    print "No user found for image (%s)\n" % filename


    def promptWithDefault(self, prompt, value):
        """Prompts the user for a value and provides a default value.
           """
        newValue = raw_input("%s [%s]: " % (prompt, value))
        if newValue == '':
            newValue = value
        elif newValue == ' ':
            newValue = ''

        return newValue



if __name__ == '__main__':
    obj = AddFSDPhoto()

