"""
Convert File
"""
import json
from neo4j import GraphDatabase


GEDCOM_FILE = 'Beck Family Tree.ged'

def parseName(nameElementDict)

def readGEDCOMfile(filename):
    file = open(GEDCOM_FILE, 'r')
    # each objects starts at level 0 and is followed by an @
    obj = file.read().split(('\n0 '))
    file.close()
    return obj

def splitElement(element):
    #split an element into Key:Value or
    #parent : [sub-elelment]

    if len(element.strip())==0:
        # do nothing !
        return [0,0]
    
    try:
        [a, b] = element.replace('\n',' \n').lstrip().split(' ',1)
    except ValueError:
        return [0,0]
    else:
        return [a,b]


def insertObject(keyStr, value, objDict):
    if keyStr in objDict.keys():
        #is it already a list
        if type(objDict[keyStr]) is list:
            objDict[keyStr].append(value)
        else:
           #make it a list
           newList = []
           # get existing key/value
           newList.append(objDict.pop(keyStr))
           # add the new value to the list
           newList.append(value)
           objDict.update({keyStr:newList})
    else:
        newList = []
        newList.append(value)
        objDict.update({keyStr:newList})
    return objDict

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



def parseObject(obj, level=0):
    objDict = {}
    objArray = obj.split('\n'+str(level+1)) 

    if level == 0:
        idLine = objArray.pop(0)
        [id, elementType] = splitElement(idLine)
        objDict = insertObject(elementType.strip(), id.strip(), objDict)
        #objDict.update({type.strip():id.strip()})
        #objDict.update({'ElementType':type})

    for element in objArray:
        if element.count('\n')==0:
            # simple element
            [keyString, valueString] = splitElement(element)
            if keyString != 0:
                objDict.update({keyString.strip() : valueString})

        else:
            # element has sub-elements
            # check if first line has TAG + VALUE
            # **************** HERE ***************

            [parent, children] = splitElement(element)
            subElem = parseObject(children, level+1)
            if parent != 0:
                objDict = insertObject(parent.strip(), subElem, objDict)
                #objDict.update({parent:subElem})
    return objDict
# --

OBJECTS = readGEDCOMfile(GEDCOM_FILE)



tree = []


for i in range(1,len(OBJECTS)):
    tree.append(parseObject(OBJECTS[i], 0))


#print(json.dumps(tree))

for elem in tree:
    if 'INDI' in elem.keys():
        [firstname, lastname, fullname] = parseName(elem["NAME"])
        print([firstname, lastname, fullname])



# DATABASE STUFF

def addIndividualToGraph(tx, individual):
    # individual is a dict that needs at a mininmum
    # - ancestryID
    # - sex
    # - name
    result = tx.run("match (a:Male {firstname: $name}) return a.firstname as firstname, ID(a) as id",
                    name=individual)
    return result 

#driver = GraphDatabase.driver("bolt://192.168.2.130:7687")


#with driver.session() as session:
   # result = session.read_transaction(addIndividualToGraph, 'Roland')
 #   for record in result: 
 #       print(record )