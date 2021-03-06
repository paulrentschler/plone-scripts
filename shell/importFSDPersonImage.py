#!/usr/bin/env python

"""Command line script for importing images of people into their
   Faculty/Staff Directory person objects in a Plone site.
   
   Use AT YOUR OWN RISK! Suggestions and improvements welcome.
   
   Requires: Plone 3.x or greater website (plone.org)
             Faculty/Staff Directory 2.x or greater (http://plone.org/products/faculty-staff-directory)
             Web Services API for Plone (http://plone.org/products/wsapi4plone.core)
   
   Notes: - images must be sized prior to importing via this script
          - images must end in .jpg, .png, or .gif - modify isValidImage() to change
          - images must be named with the person object's ID and the extension
          - may not work with a folder that has a large number of image files
   
   Paul Rentschler <par117@psu.edu>
   """

import os
import datetime
import argparse
import getpass
from xmlrpclib import ServerProxy
from xmlrpclib import Binary


class AddFSDPhotos(object):
    # optionally specify default options here
    host = 'localhost'
    port = '8080'
    fsd = '/huck/people'
    imageDirectory = '/import'
    user = 'admin'
    password = ''  # don't specify a password, that's just bad :(
    ploneClient = False
    args = []


    def __init__(self):
        """Processes the command line arguments and stores the values provided.
           """
        parser = argparse.ArgumentParser()
        parser.add_argument("-i", "--images", 
                            help="directory that contains the images to import")
        parser.add_argument("-s", "--siteurl",
                            help="url, port, and path to the FSD directory in " +
                                 "the site. example: " +
                                 "http://localhost:8080/plone/people")
        parser.add_argument("-u", "--username",
                            help="zope level user to log in as")
        parser.add_argument("-p", "--password",
                            help="password for the zope level user")
        parser.add_argument("-d", "--delete", action="store_true",
                            help="delete images after successful import")
        parser.add_argument("-o", "--overwrite", action="store_true",
                            help="overwrite images if already present")
        self.args = parser.parse_args()
        
        self.announce()
        self.confirmSettings()
        print "importing from: %s\n" % self.imageDirectory
        
        # create the connection to the Plone site
        if self.connectToPlone():
            self.processDirectory()
        else:
            print "ERROR: failed to connect to the Plone site"
        print


    def announce(self):
        """Prints an initial message announcing the script
           """
        now = datetime.datetime.now()
        print "\nFaculty/Staff Directory Image Importer:",
        print now.strftime("%a %e %b %Y - %H:%M:%S")
        print


    def confirmSettings(self):
        """Confirms that we have all the settings needed to run the script
           and prompts the user if we don't
           """
        # store the image directory
        if self.args.images is not None and self.args.images != "":
            self.imageDirectory = self.args.images
        else:
            self.imageDirectory = self.promptWithDefault(
                "Enter the path to the directory with the images " +
                "(ex: /home/user/images)",
                self.imageDirectory)
            
        # separate the host, port, and fsd path from the url argument
        if self.args.siteurl is not None and self.args.siteurl != "":
            self.host, self.port = self.args.siteurl.strip('http://').split(':')
            self.port, self.fsd = self.port.split('/', 1)
            self.fsd = '/' + self.fsd
        else:
            self.host = self.promptWithDefault(
                "What is the host name for the server (ex: localhost)",
                self.host)
            self.port = self.promptWithDefault(
                "What port is Zope running on (ex: 8080)", self.port)
            self.fsd = self.promptWithDefault(
                "What is the path to the FSD directory (ex: /plone/people)",
                self.fsd)
            
        # store the username
        if self.args.username is not None and self.args.username != "":
            self.user = self.args.username
        else:
            self.user = self.promptWithDefault(
                "Enter the ZMI username to connect as", self.user)
                
        # store the password
        if self.args.password is not None and self.args.password != "":
            self.password = self.args.password
        else:
            self.password = getpass.getpass("Enter the ZMI password: ")


    def connectToPlone(self):
        """Connect to the specified plone site with the provided credentials
           and set the client reference.
           """
        ploneSite, path = self.fsd[1:].split('/', 1)
        connectString = "http://%s:%s@%s:%s/%s" % (self.user, self.password,
                                                   self.host, self.port,
                                                   ploneSite)
        try:
            self.ploneClient = ServerProxy(connectString)
            # attempt to get the plone site as a test of the connection
            try:
                site = self.ploneClient.get_object([self.fsd])
                return True
            except:
                return False
        except:
            return False


    def getFullPath(self, filename):
        """Generates the full path and filename for the given filename using
           the imageDirectory property.
           """
        path = self.imageDirectory
        if path[0:-1] != "/":
            path += "/"
        return path + filename


    def importImage(self, filename):
        """Imports the image into the FSD person object
           """
        digitalId, extension = filename.rsplit('.', 1)
        personPath = "%s/%s" % (self.fsd, digitalId)
        try:
            image = open(self.getFullPath(filename))
            personData = { personPath: [
                { 'image': Binary(image.read()) },
                'FSDPerson',
            ]}
        except IOError:
            print "couldn't open image file"
            
        try:
            # get the current FSD person object
            personObj = self.ploneClient.get_object([personPath])
            if personObj[personPath][0]['image'] != '':
                if not self.args.overwrite:
                    print "image exists (use -o to overwrite)"
                else:
                    self.updatePerson(personData, filename)
            else:
                self.updatePerson(personData, filename)
        except:
            print "no user found"


    def isValidImage (self, filename):
        """Determines if the image is valid by looking at the filename extension
           """
        validExtensions = ['jpg', 'png', 'gif']
        name, extension = filename.rsplit('.', 1)
        if extension in validExtensions:
            return True
        return False


    def processDirectory(self):
        """Processes the image directory and imports any images into the
           Faculty/Staff Directory of the Plone site
           """
        # verify that the image directory exists
        if os.path.exists(self.imageDirectory):
            if len(os.listdir(self.imageDirectory)) == 0:
                print "No files to process"
            else:
                for filename in os.listdir(self.imageDirectory):
                    print filename + " -",
                    if not self.isValidImage(filename):
                        print "invalid image format"
                    else:
                        self.importImage(filename)


    def promptWithDefault(self, prompt, value):
        """Prompts the user for a value and provides a default value.
           """
        newValue = raw_input("%s [%s]: " % (prompt, value))
        if newValue == '':
            newValue = value
        elif newValue == ' ':
            newValue = ''
        return newValue


    def updatePerson(self, personData, filename):
        """Updates the person object with personData and deletes filename
           if successful and -d is set
           """
        try:
            self.ploneClient.put_object(personData)
            print "updated",
            if self.args.delete:
                os.remove(self.getFullPath(filename))
                print "- file deleted"
            else:
                print
        except:
            print "upload failed"



if __name__ == '__main__':
    obj = AddFSDPhotos()

