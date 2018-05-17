#!/usr/bin/env python3

import requests
import argparse
import igraph
import neo4j.v1


def query_pubmed_elink(pubmed_id,linkname):
  print("Querying pubmed for links "+linkname+" of "+str(pubmed_id))
  parameters = {
    'db':'pubmed',
    'id':pubmed_id,
    'linkname':linkname,
    'retmode':'json',
    'tool':tool,
    'email':email,
    }
  r = requests.get(
    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi',
    params=parameters)
  return(r.json())

def query_pubmed_esummary(pubmed_id):
  print("Querying pubmed for summary of "+str(pubmed_id))
  parameters = {
    'db':'pubmed',
    'id':pubmed_id,
    'retmode':'json',
    'tool':tool,
    'email':email,
    }
  r = requests.get(
    'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',
    params=parameters)
  return(r.json())

class Deal_with_neo4j(object):
  def __init__(self,uri="bolt://localhost:7687",
               user="neo4j",password="insecure"):
    self._driver = neo4j.v1.GraphDatabase.driver(uri, auth=(user, password))
  def close(self):
    self._driver.close()
  def dump_db(self):
    with self._driver.session() as session:
      with session.begin_transaction() as tx:
        result = tx.run("MATCH (n) RETURN (n)")
        return( list(result.records()) )
  def pubmed_get_metadata(self,pubmed_id,update_threshold=0):
    with self._driver.session() as session:
      with session.begin_transaction() as tx:
        test_statement = ("MATCH (a:paper {pubmed_id:{pubmed_id}})\n"
          "  WHERE a.updated > timestamp() - "
          ""+str(update_threshold)+""
          "*(1000*60*60*24*365)\n"
          "RETURN count(a)")
        if tx.run(test_statement,pubmed_id=pubmed_id).single()[0]:
          return(0)
        else:
          raw_metadata = query_pubmed_esummary(pubmed_id)['result']
          metadata = raw_metadata[raw_metadata['uids'][0]]
          statement = ("MERGE (a:paper {pubmed_id:{pubmed_id},"
            "terminal:'true',title:{title}})\n"
            "  ON CREATE SET a.updated = timestamp()"
            "  ON MATCH  SET a.updated = timestamp()")
          tx.run(statement,pubmed_id=pubmed_id,title=metadata['title'])
          return(1)
#
#        statement = "MERGE ({edge0}:paper {terminal:'true'})"+
#          "MERGE ({edge1}:paper {terminal:'true'})"+
#          "MERGE ({edge0})-[r:{type}]->({edge1})"
#        tx.run(statement,edge0=edge[0],edge1=edge[1],type="cites")
#        tx.commit_transaction()
#  pubmed_expand_from(self,pubmed_id)
  def write_edgelist(self, edgelist):
    with self._driver.session() as session:
      with session.begin_transaction() as tx:
#        statement = "MERGE ({edge0}:paper {terminal:'true'})"+
#          "MERGE ({edge1}:paper {terminal:'true'})"+
#          "MERGE ({edge0})-[r:{type}]->({edge1})"
#        tx.run(statement,edge0=edge[0],edge1=edge[1],type="cites")
#        tx.commit_transaction()
        pass

#  def print_friends_of(name):
#    with driver.session() as session:
#        with session.begin_transaction() as tx:
#            for record in tx.run("MATCH (a:Person)-[:KNOWS]->(f) "
#                                 "WHERE a.name = {name} "
#                                 "RETURN f.name", name=name):
#                print(record["f.name"])
#  print_friends_of("Alice")

#      greeting = session.write_transaction(self._create_and_return_greeting, message)
#      print(greeting)
#  @staticmethod
#  def _create_and_return_greeting(tx, message):
#    result = tx.run("CREATE (a:Greeting) "
#                    "SET a.message = $message "
#                    "RETURN a.message + ', from node ' + id(a)", 
#                    message=message)
#    return result.single()[0]


if __name__=="__main__":

# also build network of authorships in neo4j

# also, on each change to the graph, print out a csv of the pubmed ids
# that are on the edge, with titles and authors

  email = "dchmiller@gmail.com"
  tool = "phylr_v0.0"
  today = 180517

  phylr_db = Deal_with_neo4j()

  print(phylr_db.pubmed_get_metadata(26941329,update_threshold=0.5))
#  phylr_db.pubmed_expand_from(26941329)


  print()
  print(phylr_db.dump_db())

  exit(1)





  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--import_pubmed_ids',  action="store", nargs="+",
    help="Give me pubmed ids to start my search from.")
  parser.add_argument('--update_age',    action="store",
    help="How old do they have to be before I update them?"+
      "Default is no update.")
  parser.add_argument('--render_igraph', action="store_true",
    help="Should I make an igraph object from this database?")
  args = parser.parse_args()

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

