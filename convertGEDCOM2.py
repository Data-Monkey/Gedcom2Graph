"""
Convert File
    samples: https://webtreeprint.com/tp_famous_gedcoms.php
    standard: http://homepages.rootsweb.com/~pmcbride/gedcom/55gctoc.htm
    article: http://blog.bruggen.com/2014/01/leftovers-from-holidays-genealogy-graphs.html?q=family&view=magazine

add direct relationship
match (child)-[:is_child_of]->(rel:Relationship)-[:is_man_of]-(father:Male),
(rel)<-[:is_woman_of]-(mother:Female)
with child, father, mother
merge (mother)-[:is_mother_of]->(child)<-[:is_father_of]-(father)

count node types
MATCH (n) 
RETURN DISTINCT count(labels(n)), labels(n)


delete all
match (n) detach delete n

"""
import re #regex
from neo4j import GraphDatabase

#GEDCOM_FILE = 'Beck Family Tree.ged'
GEDCOM_FILE = 'royal92.ged'

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

# ------------------------------------------------------------
# DATABASE STUFF
# ------------------------------------------------------------
def addIndividualToGraph(tx, individual):
    # individual is a dict that needs at a mininmum
    # - gedcomID
    # - sex
    # - name

    # some cleanup
    
    if individual["SEX"] == 'M'  : gender = 'Male'
    elif individual["SEX"] == 'F'  : gender = 'Female'
    else : gender = 'Individual'

    [firstname, lastname, fullname] = parseName(individual["NAME"])

    gedcomID = individual["gedcomID"]


    query = "merge (a:%s {fullname:'%s', firstname:'%s', lastname:'%s', gedcomID:'%s'}) return ID(a) as dbID" %(gender,
                    fullname,
                    firstname,
                    lastname,
                    gedcomID)
    
    result = tx.run(query)
    
    return result 

def addFamilyToGraph(tx, family):
    # build the query to create the family
    # find family members
    query = []
    wth = ['with']

    if 'WIFE' in family.keys():
        query.append ("match (wife {gedcomID:'%s'})"%(family['WIFE']))
        wth.append('wife')
    if 'HUSB' in family.keys():
        query.append ("match (husb {gedcomID:'%s'})"%(family['HUSB']))  
        wth.append('husb')
    if 'CHIL' in family.keys():
        i=0
        for child in family['CHIL']:
            i=i+1
            query.append ("match (c%s {gedcomID:'%s'})"%(str(i),child['CHIL']))
            wth.append('c'+str(i))

    # build with string
    query.append(','.join(wth).replace(',',' ',1))
    
    # create relationship node if it does not exist
    query.append("merge (r:Relationship {gedcomID:'%s'})"%(family['gedcomID']))

    # create links
    if 'WIFE' in family.keys():
        query.append ("merge  (wife) -[:is_woman_of]-> (r)")
    if 'HUSB' in family.keys():
        query.append ("merge (husb) -[:is_man_of]-> (r)")
    if 'CHIL' in family.keys():
        i=0
        for child in family['CHIL']:
            i=i+1
            query.append ("merge  (c%s)  -[:is_child_of]-> (r) "%(str(i)))
            

    qry = '\n'.join(query)
    print (qry)
    print ('----------------')
    result = tx.run(qry)
    
    return result    



# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

DATALIST = readGEDCOMfile(GEDCOM_FILE)

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

# print(persons)


driver = GraphDatabase.driver("bolt://192.168.2.130:7687")
with driver.session() as session:
    for person in persons:
        result = session.write_transaction(addIndividualToGraph, person)
    for family in families:
        result = session.write_transaction(addFamilyToGraph, family)
