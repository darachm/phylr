#!/usr/bin/env python3

import requests
import argparse
import igraph
import neo4j.v1
import time

def query_pubmed_elink(pubmed_id,linkname):
  global last_query
  print("Querying pubmed for links "+linkname+" of "+str(pubmed_id))
  parameters = {
    'db':'pubmed',
    'id':pubmed_id,
    'linkname':linkname,
    'retmode':'json',
    'tool':tool,
    'email':email,
    }
  while ( time.time() < last_query + request_frequency ):
    time.sleep(0.1)
  r = requests.get(
    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi',
    params=parameters)
  last_query = time.time()
  return(r.json())

def query_pubmed_esummary(pubmed_id):
  global last_query
  print("Querying pubmed for summary of "+str(pubmed_id))
  parameters = {
    'db':'pubmed',
    'id':pubmed_id,
    'retmode':'json',
    'tool':tool,
    'email':email,
    }
  while ( time.time() < last_query + request_frequency ):
    time.sleep(0.1)
  r = requests.get(
    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',
    params=parameters)
  last_query = time.time()
  return(r.json())

class Deal_with_neo4j(object):

  def __init__(self,uri="bolt://localhost:7687",
               user="neo4j",password="insecure"):
    self._driver = neo4j.v1.GraphDatabase.driver(uri, auth=(user, password))
    with self._driver.session() as session:
      with session.begin_transaction() as tx:
        tx.run("CREATE CONSTRAINT ON (n:paper) ASSERT n.pubmed_id IS UNIQUE;")

  def close(self):
    self._driver.close()

  def dump_db(self):
    with self._driver.session() as session:
      result = session.run("MATCH (n) RETURN (n)") #not tested recently 
      return( list(result.records()) )


  def pubmed_expand_from(self,pubmed_id,update_threshold=0.5):

    self.pubmed_get_metadata(pubmed_id)

    leaves = []

    with self._driver.session() as session:
      test_return = self._property_is_current(session,
        pubmed_id,"expanded_to",update_threshold=update_threshold)
    if test_return:
      print(str(pubmed_id)+" expanded_to is current, not updated")
    else:
      with self._driver.session() as session:
        raw_citedin = query_pubmed_elink(pubmed_id,
          "pubmed_pubmed_citedin")
        try:
          list_citedin = raw_citedin["linksets"][0]["linksetdbs"][0]["links"]
          for upstream in list_citedin:
            session.run("MERGE (a:paper {pubmed_id:{pubmed_id}})",
              pubmed_id=upstream) 
            session.run("MERGE (a:paper {pubmed_id:{pubmed_id}})"
              " ON MATCH SET a.expanded_to = timestamp()",
              pubmed_id=pubmed_id) 
            session.run("MATCH (a:paper {pubmed_id:{node0_id}}),"
              "(b:paper {pubmed_id:{node1_id}})\n"
              "MERGE (a)-[r:cites]->(b)",
              node0_id=upstream,node1_id=pubmed_id)
          leaves.extend(list_citedin)
        except:
          pass

    with self._driver.session() as session:
      test_return = self._property_is_current(session,
        pubmed_id,"expanded_from",update_threshold=update_threshold)
    if test_return:
      print(str(pubmed_id)+" expanded_from is current, not updated")
    else:
      with self._driver.session() as session:
        raw_refs = query_pubmed_elink(pubmed_id,
          "pubmed_pubmed_refs")
        try:
          list_refs = raw_refs["linksets"][0]["linksetdbs"][0]["links"]
          for downstream in list_refs:
            session.run("MERGE (a:paper {pubmed_id:{pubmed_id}})"
              " ON MATCH SET a.expanded_from = timestamp()",
              pubmed_id=pubmed_id) 
            session.run("MERGE (a:paper {pubmed_id:{pubmed_id}})",
              pubmed_id=downstream) 
            session.run("MATCH (a:paper {pubmed_id:{node0_id}}),"
              "(b:paper {pubmed_id:{node1_id}})\n"
              "MERGE (a)-[r:cites]->(b)",
              node0_id=pubmed_id,node1_id=downstream)
          leaves.extend(list_refs)
        except:
          pass

    for i in leaves:
      with self._driver.session() as session:
        session.run("MERGE (a:paper {pubmed_id:{pubmed_id}})"
          " ON MATCH SET a.leaf = 1",
          pubmed_id=i) 

    with self._driver.session() as session:
      session.run("MERGE (a:paper {pubmed_id:{pubmed_id}})"
        " ON MATCH SET a.leaf = 0",
        pubmed_id=pubmed_id) 

    return(leaves)

  @staticmethod
  def _property_is_current(session,pubmed_id,which_property,
                           update_threshold=0.0):
    result = session.run("MATCH (a:paper {pubmed_id:"+str(pubmed_id)+"})\n"
      "  WHERE coalesce(a."+which_property+",0) > timestamp() - "
      ""+str(update_threshold)+"" # so this is the year past
      "*(1000*60*60*24*365)\n"
      "RETURN count(a)")
    return(result.single()[0])

  def pubmed_get_metadata(self,pubmed_id,update_threshold=0.5):
    with self._driver.session() as session:
      if self._property_is_current(session,
          pubmed_id,"updated",update_threshold=update_threshold):
        return(0)
      else:
        raw_metadata = query_pubmed_esummary(pubmed_id)['result']
        metadata = raw_metadata[raw_metadata['uids'][0]]
        statement = ("MERGE (a:paper {pubmed_id:{pubmed_id}})"
          "  SET a.title = {title}\n"
          "  SET a.updated = timestamp()")
        session.run(statement,pubmed_id=pubmed_id,title=metadata['title'])
        return(0)

  def get_leaf_list(self):
    with self._driver.session() as session:
      result = session.run("MATCH (a:paper) WHERE a.leaf > 0 "
        "RETURN a.pubmed_id")
      return(list(result.records()))


if __name__=="__main__":

# also build network of authorships in neo4j

# also, on each change to the graph, print out a csv of the pubmed ids
# that are on the edge, with titles and authors

  email = "dchmiller@gmail.com"
  tool = "phylr_v0.0"

  last_query = time.time()
  request_frequency = 1 # second

  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--import_pubmed_ids',  action="store", nargs="+",
    help="Give me pubmed ids to start my search from.")
  parser.add_argument('--update_age',    action="store",
    help="How old do they have to be before I update them?"+
      "Default is no update.")
  parser.add_argument('--render_igraph', action="store_true",
    help="Should I make an igraph object from this database?")
  args = parser.parse_args()

  phylr_db = Deal_with_neo4j()

  first_leaves = []

  for each_query in args.import_pubmed_ids:
    first_leaves.extend(phylr_db.pubmed_expand_from(each_query))

  these_new_leaves = first_leaves
  for i in range(1):
    this_batch = these_new_leaves
    these_new_leaves = []
    for each_leaf in this_batch:
      these_new_leaves.extend(phylr_db.pubmed_expand_from(each_leaf))

  for j in [i[0] for i in phylr_db.get_leaf_list()]:
    phylr_db.pubmed_get_metadata(j)

  exit(0)






  article_metadata = {}
  graph_list = []

  if args.import_pubmed_ids:
    print("I'm going to add these pubmed ids to the database:")
    print(args.import_pubmed_ids)


  
  for i in args.pubmed_ids:

    raw_metadata = query_pubmed_esummary(i)['result']
    metadata = raw_metadata[raw_metadata['uids'][0]]
    article_metadata[i] = {'title':metadata['title']}#,'all_metadata':metadata}

    raw_refs = query_pubmed_elink(i,'pubmed_pubmed_refs')
    refs = raw_refs['linksets'][0]['linksetdbs'][0]['links']
    for j in refs:
      graph_list.append( (i,j) )

    raw_citedby = query_pubmed_elink(i,'pubmed_pubmed_citedin')
    citedby = raw_citedby['linksets'][0]['linksetdbs'][0]['links']
    for j in citedby:
      graph_list.append( (j,i) )

  id_list = set()
  for i in graph_list:
    id_list.add(i[0])
    id_list.add(i[1])
  name_to_id = {}
  id_to_name = {} 
  id_counter = 0
  for vertex in id_list:
    id_to_name[id_counter] = vertex
    name_to_id[vertex] = id_counter
    id_counter += 1

  for i in id_list:
    raw_metadata = query_pubmed_esummary(i)['result']
    metadata = raw_metadata[raw_metadata['uids'][0]]
    article_metadata[i] = {'title':metadata['title']}#,'all_metadata':metadata}

  sanitary_edge_list = []
  for i, edge in enumerate(graph_list):
    sanitary_edge_list.append((name_to_id[edge[0]],name_to_id[edge[1]]))

  g = igraph.Graph(sanitary_edge_list,directed=True)

  g.simplify(combine_edges=max)
  g.vs["name"] = [ id_to_name[v.index] for v in list(g.vs) ]
  g.vs["label"] = [ article_metadata[i]['title'] for i in g.vs["name"] ]

  layout = g.layout("kk")
  igraph.plot(g, "tmp.png", layout = layout)

