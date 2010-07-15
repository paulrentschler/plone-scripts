#!/usr/bin/env python

""" 
A module for creating the yearly folders that live under each
calendar event grouping and seminar series folder.

Uses the Web Services API for Plone so that the script can
be run locally.

Written by: Paul Rentschler (par117@psu.edu)
Created on: 14 July 2010
"""

from xmlrpclib import ServerProxy
from xmlrpclib import DateTime
import datetime


def addYearFolders():
    """
Looks at all the folders in the /calendar folder and adds
the appropriate next year subfolder to folders that already
have a subfolder for the current year.
"""

    # create a connection to the plone site
    client = connectToPlone('localhost', '8080', '/huck')
    
    if type(client) == type(False):
        print "No connection to the Plone site could be made.\n"
        
    else:
        thisYear = datetime.datetime.now().year
        
        #processFolder(client, '/huck/calendar', thisYear)
        #processFolder(client, '/huck/calendar/other-types-of-event', thisYear)
        #processFolder(client, '/huck/calendar/training-and-orientation-events', thisYear)
        processFolder(client, '/huck/calendar/conferences-and-workshops', thisYear)


    print "Done!\n\n"
    
    
    

def processFolder(client, folderUrl, thisYear):
    """
Looks at the specified folder to see if next year subfolders need to
be added. If no year folders exist, then it recursively processes
the subfolders.
"""

    # define next year based on the provided "thisYear"
    nextYear = thisYear + 1

    # get the folder object referenced by the provided url
    print "Getting: %s" % folderUrl
    folder = client.get_object([folderUrl])[folderUrl]
    
    # make sure that the folderUrl really referenced a folder
    if folder[1] == 'Folder':
        # see if the yearly subfolders exist
        thisYearExists = False
        nextYearExists = False
        existingYears = []
        years = range(2007, nextYear)
        for subfolder in folder[2]['contents'].keys():
            for year in years:
                if str(year) in subfolder:
                    existingYears.append(year)
                    if year == thisYear:
                        thisYearExists = True
                    elif year == nextYear:
                        nextYearExists = True

        if thisYearExists and not nextYearExists:
            # see if there are events
            thisYearFolderUrl = folderUrl + '/' + str(thisYear)
            thisYearFolder = client.get_object([thisYearFolderUrl])[thisYearFolderUrl]
            
            if thisYearFolder[1] == 'Folder' and len(thisYearFolder[2]['contents'].keys()) > 1:
                # this year's folder exists and has events: create next year's folder
                addNextYearFolder(client, folderUrl, thisYear)
                
            elif thisYearFolder[1] == 'Folder':
                create = raw_input("This year's folder exists but has no events, do you want to create a folder for next year? (y/n) ")
                if create.lower() == 'y':
                    # create next year's folder
                    addNextYearFolder(client, folderUrl, thisYear)
                    
        elif not thisYearExists and not nextYearExists and len(existingYears) == 0:
            print "recursively process each subfolder"
            for subfolder in folder[2]['contents'].keys():
                processFolder(client, subfolder, thisYear)




def addNextYearFolder(client, folderUrl, thisYear):
    """
Adds a subfolder to the specified folder that is based on
the specified current year folder.
"""

    # define next year based on the provided "thisYear"
    nextYear = thisYear + 1
    
    # define the folder urls for the years
    thisYearFolderUrl = folderUrl + '/' + str(thisYear)
    nextYearFolderUrl = folderUrl + '/' + str(nextYear)


    # get the folder definition for thisYear
    thisYearFolder = client.get_object([thisYearFolderUrl])[thisYearFolderUrl]
    
    # create the nextYear folder
    properties = {}
    properties['locallyAllowedTypes'] = thisYearFolder[0]['locallyAllowedTypes']
    properties['immediatelyAddableTypes'] = thisYearFolder[0]['immediatelyAddableTypes']
    properties['description'] = thisYearFolder[0]['description'].replace(str(thisYear), str(nextYear)).strip()
    properties['title'] = str(nextYear)
    properties['id'] = str(nextYear)
    
    # add the nextYear folder to the site
    nextYearFolder = { nextYearFolderUrl : [properties, 'Folder', {}] }
    client.post_object(nextYearFolder)
    
    
    # get the collection definition for thisYear
    thisYearCollection = client.get_object([thisYearFolderUrl + '/full-list'])[thisYearFolderUrl + '/full-list']
    
    # create the nextYear collection
    properties = {}
    properties['id'] = 'full-list'
    properties['title'] = thisYearCollection[0]['title'].replace(str(thisYear), str(nextYear)).strip()
    properties['description'] = thisYearCollection[0]['description'].replace(str(thisYear), str(nextYear)).strip()
    
    criteria = thisYearCollection[2]['criteria']
    criteria['crit__end_ATDateRangeCriterion']['start']['value'] = DateTime(datetime.datetime(nextYear, 1, 1, 0, 0, 0))
    criteria['crit__end_ATDateRangeCriterion']['end']['value'] = DateTime(datetime.datetime(nextYear, 12, 31, 11, 55, 0))
    
    # add the nextYear collection to the site
    nextYearCollection = { nextYearFolderUrl + '/full-list' : [properties, 'Topic', { 'criteria' : criteria }] }
    client.post_object(nextYearCollection)
    
    






def connectToPlone(host, port, ploneSiteUrl):
    """
Prompt the user for the ZMI admin password and create a connection
to the specified Plone site
"""
    pw = raw_input("What is the admin password to the ZMI? ")
    connectString = "http://admin:%s@%s:%s%s" % (pw, host, port, ploneSiteUrl)
    try:
        client = ServerProxy(connectString)
    except:
        client = False

    return client




# run the main method if this file is called as a shell script
if __name__ == '__main__':
    addYearFolders()
