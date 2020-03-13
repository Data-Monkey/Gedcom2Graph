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


import parseGEDCOM as pg
import loadGRAPH as lg

#GEDCOM_FILE = 'Beck Family Tree.ged'
GEDCOM_FILE = 'royal92.ged'


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

[persons, families] = pg.parseGEDCOM(GEDCOM_FILE)
print(persons)

# Load to Graph Database
lg.loadPersons(persons)
lg.loadPersons(persons)