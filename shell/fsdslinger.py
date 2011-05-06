"""
Bulk Import of Faculty Staff Directory People and Images.

Special thanks to kevin7kal for his WebSlinger project which
served as a basis for this code.
https://weblion.psu.edu/trac/weblion/browser/weblion/WebSlinger
"""
from time import time
from datetime import datetime
#from xmlrpclib import Binary

from logging import getLogger
#from PIL import Image

import csv

#from wsapi4plone.client import getClient
from xmlrpclib import ServerProxy



class FSDslinger(object):
        '''an class for bulk import of Faculty Staff Directory people and images into a Plone site'''

        logger = getLogger('FSDSlinger')
        fieldnamesMap = {}
        classificationsMap = {}
        specialtiesMap = {}


        def __init__(self):
            # indicate that we do not have a connection yet
            self.connected = False
            self.client = False



        def connectToPlone(self, username, password, host, port, ploneSite):
            """Connect to the specified plone site with the provided credentials
               and set the client reference.
               """
            connectString = "http://%s:%s@%s:%s%s" % (username, password, host, port, ploneSite)
            try:
                #from xmlrpclib import Server
                self.client = ServerProxy(connectString, allow_none=True)
                self.connected = True
            except:
                self.client = False
                self.connected = False



        def fsdPeopleSling(self, pathToFsd, fsdName, csvFile):
            """Bulk import of faculty staff directory people from a csv file
                  * fsdPath: the path from the Plone site root to the FSD folder
                  * csvFile: the CSV file to import the people form
               """
            # get the specialties and classifications from the site if not specified
            if len(self.specialtiesMap) == 0:
                self._getFsdSpecialties()
                
            if len(self.classificationsMap) == 0:
                self._getFsdClassifications()
            
            # build a list of dictionary objects from the CSV file
            fsdData = self._buildFsdData(csvFile)
            
            # update the people in FSD
            self._updateFsdPeople(pathToFsd, fsdName.lower(), fsdData)



        def _updateFsdPeople(self, pathToFsd, fsdName, fsdData ):
            """Add the people to the Faculty Staff Directory by either
               inserting them as new people or updating existing people.
               """
            facultyandstaff = {}
            
            for person in fsdData:
                fsdPersonObj = self._createPersonObject(fsdName, person)
                try:
                    print "Adding %s to FSD..." % person['id']
                    response = self.client.post_object(fsdPersonObj)
                except:
                    print "Person %s already exists in the FSD, updating instead..." % person['id']
                    combinedPerson = self._updateExistingPerson(person)
                    if len(combinedPerson.keys()) > 0:
                        fsdPersonObj = self._createPersonObject(fsdName, combinedPerson)
                        response = self.client.put_object(fsdPersonObj)
                    else:
                        print "There was nothing to update for %s" % person['id']
                    pass



        def _createPersonObject(self, fsdName, personData):
            """Converts the personData dictionary data into the proper format for
               a FSD person object in the Plone site.
               """
            fsdPersonObj = {}
            fsdPersonObj[fsdName+'/'+personData['id']] = [personData, 'FSDPerson']
            return fsdPersonObj



        def _getFsdSpecialties(self):
            """Get all the FSD Specialties from the Plone site and create a
               map between the Title and the UID.
               """
            specialties = self.client.query({'Type':'Specialty'})
            for url, specialty in specialties.items():
                self.specialtiesMap[specialty['Title']] = specialty['UID']



        def _getFsdClassifications(self):
            """Get all the FSD Classifications from the Plone site and create a
               map between the Title and the UID.
               """
            classifications = self.client.query({'Type':'Classification'})
            for url, classification in classifications.items():
                self.classificationsMap[classification['Title']] = classification['UID']



        def _buildFsdData(self, csvFile):
            """Build a data tree structure for the FSD directory.
               The data structure is a list of dictionaries.
               """
            # read from the CSV file
            file = open(csvFile, 'rbU')
            csvPeople = csv.DictReader(file)

            fsdPeople = []
            for person in csvPeople:
                # alter the field names for a person
                fsdPerson = {}
                for key, value in person.items():
                    try:
                        fsdPerson[self.fieldnamesMap[key]] = value
                    except KeyError:
                        print "No key [%s] in the fieldnames map" % key
                        pass

                # add the person's classification
                if 'Classification' in person and person['Classification'] != '':
                    try:
                        fsdPerson['classifications'] = [self.classificationsMap[person['Classification']]]
                    except:
                        # the person doesn't have a classification
                        pass

                # add the person's specialty
                if 'Specialties' in person and person['Specialties'] != '':
                    personSpecialties = person['Specialties'].split(',')
                    for personSpecialty in personSpecialties:
                        try:
                            fsdPerson['specialties'].append(self.specialtiesMap[personSpecialty])
                        except:
                            fsdPerson['specialties'] = [self.specialtiesMap[personSpecialty]]

                # add the advisors
                if 'Advisors' in person and person['Advisors'] != '':
                    # get the UID for the faculty classification
                    facultyClassification = self.client.query({'Type': 'Classification', 'id': 'faculty'})
                    facultyClassificationUID = facultyClassification[facultyClassification.keys()[0]]['UID']

                    # break up advisors by & sign
                    advisors = person['Advisors'].split("&")

                    # process each advisor
                    print "Determining the advisors for %s..." % fsdPerson['id']
                    for advisor in advisors:
                        advisorBrains = self.client.query({
                            'Type': 'Person', 
                            'Title': advisor.strip(),
                            'getRawClassifications': facultyClassificationUID
                            })
                        if len(advisorBrains) == 1:
                            # we have only one hit, set the advisor
                            try:
                                fsdPerson['advisors'].append(advisorBrains[advisorBrains.keys()[0]]['UID'])
                            except:
                                fsdPerson['advisors'] = [ advisorBrains[advisorBrains.keys()[0]]['UID'] ]
                        else:
                            print "  - could not find an accurate advisor match for '%s'." % advisor.strip()

                # fix the job title
                if 'jobTitles' in fsdPerson and fsdPerson['jobTitles'] != '':
                    fsdPerson['jobTitles'] = [fsdPerson['jobTitles']]

                #fix the campus
                if 'campus' in fsdPerson and fsdPerson['campus'] != '':
                    fsdPerson['campus'] = [fsdPerson['campus'], '']

                # add the various web sites together
                websiteKeys = ['Personal website', 'Lab website', 'Other website']
                for websiteKey in websiteKeys:
                    if websiteKey in person and person[websiteKey] != '':
                        try:
                            fsdPerson['websites'].append(person[websiteKey])
                        except:
                            fsdPerson['websites'] = [person[websiteKey]]


                # append the person to the list of people to add/update
                fsdPeople.append(fsdPerson)

            file.close()
            return fsdPeople



        def _updateExistingPerson(self, newPersonData):
            """Gets the data for the existing person object and adds/updates the
               information based on what is contained in the newPersonData dictionary.
               """
            # get the existing person object from the Plone site
            existingPersonBrain = self.client.query({'Type': 'Person', 'id':newPersonData['id']})
            if len(existingPersonBrain) == 1:
                existingPersonObj = self.client.get_object([existingPersonBrain.keys()[0]])
                try:
                    existingPersonData = existingPersonObj[existingPersonObj.keys()[0]][0]
                    
                    # define all the fields that we will just "fill in the gaps" for
                    fillInFields = [
                        'firstName', 'middleName', 'lastName', 'suffix', 'nickName',
                        'officeAddress', 'officeCity', 'officeState', 'officePostalCode',
                        'campus', 
                        ]
                    
                    # fill in the gaps
                    for fillInField in fillInFields:
                        if fillInField in newPersonData and newPersonData[fillInField] != "":
                            # we have data, see if we can include it
                            if fillInField in existingPersonData and existingPersonData[fillInField] == "":
                                # the field is blank, so we can fill it in
                                existingPersonData[fillInField] = newPersonData[fillInField]
                                
                    # add any new specialties to the person
                    if 'specialties' in newPersonData:
                        for specialtyUID in newPersonData['specialties']:
                            if specialtyUID not in existingPersonData['specialties']:
                                # specialty not already assigned, assign it
                                existingPersonData['specialties'].append(specialtyUID)
                                
                    # add any new classifications to the person
                    if 'classifications' in newPersonData:
                        for classificationUID in newPersonData['classifications']:
                            if classificationUID not in existingPersonData['classifications']:
                                # classification not already assigned, assign it
                                existingPersonData['classifications'].append(classificationUID)
                                
                    # add any new advisors to the person
                    if 'advisors' in newPersonData:
                        for advisorUID in newPersonData['advisors']:
                            if advisorUID not in existingPersonData['advisors']:
                                # advisor not already assigned, assign it
                                existingPersonData['advisors'].append(advisorUID)
                                
                    # add any new job titles to the person
                    jobTitles = []
                    for jobTitle in existingPersonData['jobTitles']:
                        if "Graduate student" in newPersonData['jobTitles'] and "graduate student" not in jobTitle.lower():
                            jobTitles.append(jobTitle)
                        
                    if 'jobTitles' in newPersonData:
                        for jobTitle in newPersonData['jobTitles']:
                            if jobTitle not in jobTitles:
                                # the job title does not exist, add it
                                jobTitles.append(jobTitle)
                    existingPersonData['jobTitles'] = jobTitles
                                
                    # add any new web sites to the person
                    if 'websites' in newPersonData:
                        for website in newPersonData['websites']:
                            if website not in existingPersonData['websites']:
                                # the web site does not exist, add it
                                existingPersonData['websites'].append(website)
                                
                    # TODO: find a better solution than this hack!
                    # Plone complains about the format of the dateTime values, so
                    #   I'm just eliminating them from the object.
                    fieldsToIgnore = [
                        'effectiveDate', 'creation_date', 'modification_date', 'expirationDate',
                        ]
                    for fieldToIgnore in fieldsToIgnore:
                        try:
                            del existingPersonData[fieldToIgnore]
                        except:
                            pass
                            
                    # TODO: having an image field also causes a problem.
                    try:
                        del existingPersonData['image']
                    except:
                        pass
                        
                except:
                    pass
                
            return existingPersonData
