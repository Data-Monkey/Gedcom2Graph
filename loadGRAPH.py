"""
load GEDCOM data structures to graph (Neo4j)
"""
from neo4j import GraphDatabase
import parseGEDCOM as pg  # THIS NEEDS TO MOVE OUT!

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

    [firstname, lastname, fullname] = pg.parseName(individual["NAME"])

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


# ----------------------------------

def loadPersons(persons):
    driver = GraphDatabase.driver("bolt://192.168.2.130:7687")
    with driver.session() as session:
        for person in persons:
            result = session.write_transaction(addIndividualToGraph, person)

def loadFamilies(families):
    driver = GraphDatabase.driver("bolt://192.168.2.130:7687")
    with driver.session() as session:
        for family in families:
            result = session.write_transaction(addFamilyToGraph, family)
