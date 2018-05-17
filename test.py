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
  return(r.json())

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
  return(r.json())

if __name__=="__main__":
  parser = argparse.ArgumentParser(description='')
  parser.add_argument('--pubmed_ids', nargs="+", help='')
  args = parser.parse_args()

  article_metadata = {}
  graph_list = []
  
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

