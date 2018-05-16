#!/usr/bin/env python3

import requests


parameters = {
  'db':'pubmed',
  'id':'26941329',
  'retmode':'json',
  'tool':'testing_phylr',
  'email':'dchmiller@gmail.com'
  }
#r = requests.get(
#  'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',
#  params=parameters)



parameters = {
  'db':'pubmed',
  'id':'26941329',
  'linkname':'pubmed_pubmed_refs',
  'retmode':'json',
  'tool':'testing_phylr',
  'email':'dchmiller@gmail.com'
  }
r = requests.get(
  'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi',
  params=parameters)

print(r.url)
print(r.content)
print(r.json())
print()
print()
print()
