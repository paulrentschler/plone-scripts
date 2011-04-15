#!/usr/bin/env python

"""A module which allows for importing images for FSD people in a Plone site."""

import sys
from xmlrpclib import ServerProxy


def main():
    """Controls the main execution of the script
       """
    
    # get any command line options
    options = getCommandLineSettings()
    
    # provide the default password
    if options['password'] == '':
        options['password'] = 'XKuHyBcCYHeg'
    
    #username, password, host, port, ploneSite
    if len(options) > 0:
        client = connectToPlone( options['username'],
                                 options['password'],
                                 options['host'],
                                 options['port'],
                                 options['plonesite'] )
                                
        # make sure we have a connection
        if type(client) <> type(False):
            createPersonObject(client, fsd, id, firstName, middleName, lastName)
    
    



def getCommandLineSettings():
    """Looks for any settings that were passed on the command line and
       returns them in a dictionary
       """
    
    if len(sys.argv) > 1 and sys.argv[1] == 'help':
        displaySyntax()
        return {}

    elif len(sys.argv) > 4:
        # parameters are: plone url, directory, username, password (optional)
        host, port = sys.argv[1].strip('http://').split(':')
        port, ploneSite = port.split('/', 1)
        ploneSite = '/' + ploneSite

        # assign the other command line arguments
        imageDir = sys.argv[2]
        username = sys.argv[3]
        try:
            password = sys.argv[4]
        except IndexError:
            password = raw_input("What is the password for user (%s)? " % username)
        
        # return the values
        return { 'host': host,
                 'port': port,
                 'plonesite': ploneSite,
                 'username': username,
                 'password': password }



def uploadPersonImage(client, personId, imageFilename):
    """Uploads the image file provided to the person object
       """
    
    # attempt to read the image file
    try:                     
        image = open(imageFilename)
        
        personData = { '/person/' + personId: [{ 'image': Binary(image.read()) }, 'FSDPerson'] }
        
    except IOError:
        pass   #no image
    
    
    try:
        personObj = client.get_object(client.post_object(personData))
        print "%s %s person object created with id: %s." % (firstName, lastName, id)
    except:
        print "failed to create %s %s with ID: %s." % (firstName, lastName, id)










def connectToPlone(username, password, host, port, ploneSite):
    """Connect to the specified plone site with the provided credentials
       and return the client reference.
       """
    connectString = "http://%s:%s@%s:%s%s" % (username, password, host, port, ploneSite)
    try:
        client = ServerProxy(connectString)
    except:
        client = False

    return client



def displaySyntax():
    """
Import image files of people into the Faculty / Staff Directory of a Plone site
from the command line. Image files must be named with the ID of the FSDPerson
object in the Plone site.
    syntax: importFSDPersonImage.py <plone site> <directory> <username> <password>

    plone site     the URL, port, and path to the Plone site you want to 
                   work with
                     example: http://localhost:8080/plone
    directory      the directory that contains the images to process/import
    username       the zope level user to log in as
    password       the password for the zope level user (optional)

"""
    print displaySyntax.__doc__
    

if __name__ == '__main__':
    addUser()

