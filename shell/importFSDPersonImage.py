#!/usr/bin/env python

"""A module which allows for importing images for FSD people in a Plone site.

   TODO:
     DONE - python package for parsing command line parameters?
     - prompt for deleting files after successful upload
     DONE - test with multiple files
     DONE - delete files after successful upload
     DONE - better output for logging purposes
   """

import sys
import os
import datetime
import argparse
from xmlrpclib import ServerProxy
from xmlrpclib import Binary


class AddFSDPhotos(object):
    # optionally specify default options here
    host = 'localhost'
    port = '8080'
    fsd = '/huck/people'
    imageDirectory = '/Users/par117lsb/import'
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
            self.password = raw_input("Enter the ZMI password for %s: " %
                                      (self.user))


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
                site = self.ploneClient.get_object([ploneSite])
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
                        digitalId, extension = filename.rsplit('.', 1)
                        personPath = "%s/%s" % (self.fsd, digitalId)
                        try:
                            image = open(self.getFullPath(filename))
                            personData = { self.fsd + "/" + digitalId: [
                                { 'image': Binary(image.read()) },
                                'FSDPerson',
                            ]}
                        except IOError:
                            print "couldn't open image file"
                
                        # get the current FSD person object
                        try:
                            personObj = self.ploneClient.get_object([personPath])
                    
                            # update the FSD person's image
                            try:
                                self.ploneClient.put_object(personData)
                                print "updated",
                                os.remove(self.getFullPath(filename))
                                print "- file deleted"
                            except:
                                print "upload failed"
                    
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
    obj = AddFSDPhotos()

