#!/usr/bin/env python

"""A module to import ResearchProject objects from another Plone site."""

from xmlrpclib import ServerProxy


def transferContent ():
    """handle moving content from one Plone site to another"""
	
    # obtain the password to the production plone site
    password = raw_input("What is the admin password to the ZMI on the production site? ")
	
    source = ServerProxy('http://admin:' + password + '@localhost:91/sleic')
    dest = ServerProxy('http://admin:admin@localhost:8080/sleic')


    # get all the ResearchProjects from the source plone site
    allProjects = source.query({'portal_type' : 'ResearchProject'})
    
    # define the fields we want to preserve
    fields = ['id', 'subject', 'title', 'projectId', 'body', 'description']
    
    # loop thru each project and add it to the dest site
    for projectId in allProjects.keys():
        print "Copying: %s ... " % projectId
        
    	# get the full source object and it's values
    	origProject = source.get_object([projectId])
    	origProjectValues = origProject.values()[0][0]
    	
    	# get the state of the source object
    	origWorkflow = source.get_workflow(projectId)
    
        # throw a notice if there is a projectImage
        if origProjectValues['projectImage'] <> '':
            print " ** PROJECT IMAGE ** "
	
    	
    	# create a dictionary of values for the new object
    	newProjectValues = {}
    	for field in fields:
            newProjectValues[field] = origProjectValues[field]
    	
    	# create the new ResearchProject object
    	newProject = { origProject.keys()[0] : [newProjectValues, 'ResearchProject'] }
    	
        # add the object to the dest site
        dest.post_object(newProject)
		
        # see if we need to change the workflow
        if origWorkflow['state'] == 'private':
            dest.set_workflow('hide', projectId)
			
			
    # indicate we are done with this project
    print "Done.\n"


if __name__ == '__main__':
    transferContent()

