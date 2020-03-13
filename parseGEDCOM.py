"""
read GEDCOM file and convert it to data structures
"""

import re #regex


def parseName(name):
    # split name: "Roland /Beck/"
    # into:
    # fullname: Roland Beck
    # firstname: Roland
    # lastname: Beck
    firstname = ''
    lastname = ''
    fullname = name

    if name.find('/') > 0:
        [firstname, lastname] = name.split('/',1)
        lastname = lastname.rstrip('/')
        fullname = firstname + ' ' + lastname
    
    return [firstname, lastname, fullname]




def splitAtLevel(obj, level):
    lvl = str(level)
    objList = obj.split('\n'+lvl+' ')

    for i in range (1, len(objList)):
        objList[i]= (lvl+' '+objList[i]).strip()
    return objList


def readGEDCOMfile(filename):
    file = open(filename, 'r')
    # each objects starts at level 0 and is followed by an @
    data = file.read()
    file.close()
    RootObjects = splitAtLevel(data, 0)

    return RootObjects

def createObjectREFERENCE(objectRecord):
    # returns a generic object type dict    
    # only consider first line for SIMPLE
    obj={}
    line = objectRecord.split('\n')[0]
    elements = line.split(' ')
    lvl = elements[0]
    gedcomType = elements[1] 
    data = ' '.join(elements[2:])
    ref = data.strip('@')
    obj.update({gedcomType:ref})
    return obj

def createObjectSIMPLE(objectRecord):
    # returns a generic object type dict    
    # only consider first line for SIMPLE
    obj={}
    line = objectRecord.split('\n')[0]
    elements = line.split(' ')
    lvl = elements[0]
    gedcomType = elements[1] 
    data = ' '.join(elements[2:])
    obj.update({gedcomType:data })
    return obj

def createObjectSEX(objectRecord):
    # returns a dict for object type SEX
    obj={}
    if objectRecord.count('\n')==0:
        # simple element
        elements = objectRecord.split(' ')
        lvl = elements[0]
        gedcomType = elements[1] 
        data = ' '.join(elements[2:])
        obj.update({gedcomType:data })

    return obj

 


def createObjectByType(objectRecord):
    # identify the record type and return an appropriate dict
    lvl = int(objectRecord[0])
    line = objectRecord[:objectRecord.find('/n')]
    gedcomType = line.split(' ')[1]
    
    if   gedcomType == 'INDI': obj=createObjectINDI(objectRecord)
    elif gedcomType == 'SEX' : obj=createObjectSEX(objectRecord)
    elif gedcomType == 'NAME': obj=createObjectSIMPLE(objectRecord)
    elif gedcomType in ['HUSB','WIFE','CHIL']: obj=createObjectREFERENCE(objectRecord)
    else: obj={}
    
    return obj

def createObjectINDI(indiRecord):
    # return a dict containing the INDI Individual
    indi = {}
    lvl = int(indiRecord[0])
    elements = splitAtLevel(indiRecord, lvl+1)
    indiRoot = elements.pop(0).split(' ')
    id = indiRoot[1].strip('@')

    indi.update({'gedcomID':id})
    indi.update({'type':'Individual'})
    indi.update({'gedcomType':'INDI'})
    
    #print('root:',indiRoot)
    for element in elements:
        indi.update(createObjectByType(element))
    return indi


def createObjectFAM(objectRecord):
    # return a dict containing the INDI Individual
    obj = {}
    lvl = int(objectRecord[0])
    elements = splitAtLevel(objectRecord, lvl+1)
    famRoot = elements.pop(0).split(' ')
    id = famRoot[1].strip('@')

    obj.update({'gedcomID':id})
    obj.update({'type':'Family'})
    obj.update({'gedcomType':'FAM'})
    
    for element in elements:
        elemObj = createObjectByType(element)
        if 'CHIL' in elemObj.keys():
            #make add to list
            if 'CHIL' in obj.keys():
                obj['CHIL'].append(elemObj)
            else :
                childList = []
                childList.append(elemObj)
                obj.update({'CHIL':childList})
        else:
            obj.update(elemObj)
    return obj

def parseGEDCOM(filename):
    
    DATALIST = readGEDCOMfile(filename)

    persons = []
    families = []

    for dataitem in DATALIST:
        #elements = splitAtLevel(dataitem, 1)
        if dataitem.find('@ INDI') > 0:
            persons.append(createObjectINDI(dataitem))
        elif dataitem.find('@ FAM') > 0:
            families.append(createObjectFAM(dataitem))
        #else:
            #print(elements)
    return [persons, families]