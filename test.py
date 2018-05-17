#!/usr/bin/env python3

import requests
import argparse
import igraph

email = "dchmiller@gmail.com"
tool = "phylr_v0.0"

def query_pubmed_elink(pubmed_id,linkname):
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
  print(r.url)
  print(r.content)
  print(r.json())

def query_pubmed_esummary(pubmed_id):
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
  print(r.url)
  print(r.content)
  print(r.json())
  return(r.json())

if __name__=="__main__":
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--pubmed_ids', nargs="+", help='')
  args = parser.parse_args()

  article_metadata = {}
   = {}
  
  for i in args.pubmed_ids:
    query_pubmed_esummary(i)
    query_pubmed_elink(i,'pubmed_pubmed_refs')
    query_pubmed_elink(i,'pubmed_pubmed_citedin')



#graph_lists = append_graph_list(graph_lists,
#              ( meet ,
#                goal_vertex ), 
#              "meet", "goal", len(meet_persons)-0.1 )
#
## Build index
#  verticies = set()
#  for edge in graph_lists.el:
#    verticies.add(edge[0])
#    verticies.add(edge[1])
#  name_to_id = {}
#  id_to_name = {}
#  id_counter = 0
#  for vertex in verticies:
#    id_to_name[id_counter] = vertex
#    name_to_id[vertex] = id_counter
#    id_counter += 1
#  
#  sanitary_edge_list = []
#  edge_capacity_list = []
#  type_map = {}
#  for i, edge in enumerate(graph_lists.el):
#    sanitary_edge_list.append(( name_to_id[edge[0]], name_to_id[edge[1]] ))
#    edge_capacity_list.append(graph_lists.cl[i])
#    type_map[name_to_id[edge[0]]] = graph_lists.tl0[i]
#    type_map[name_to_id[edge[1]]] = graph_lists.tl1[i]
#
#  g = igraph.Graph(sanitary_edge_list,directed=True)
#  g.es["capacity"] = edge_capacity_list
#
#  g.simplify(combine_edges=max)
#  g.vs["type"] = [   type_map[v.index] for v in list(g.vs) ]
#  g.vs["name"] = [ id_to_name[v.index] for v in list(g.vs) ]
#  g.vs["label"] = g.vs["name"]
#
