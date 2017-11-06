from newspaper import Article
from neo4j.v1 import GraphDatabase, basic_auth

from pymong import MongoClient


neoDriver = GraphDatabase.driver("bolt://35.197.26.251:7687", auth=basic_auth("neo4j", "edupassword"))

mongoDriver = MongoClient('mongodb://35.197.88.141:27017/')
mongoTable = mongoDriver["test"]["Sources"]


def dbSearch(searchString):
   keywords = searchString.split(" ")
   results = neoDriver.session().run( \
   "MATCH (b:Keyword)\n" + \
   "WHERE b.name in $keywords\n" + \
   "MATCH (a:Article)-[h:Has]->(b)\n" + \
   "WITH a, sum(h.certainty) AS rank\n" + \
   "return a ORDER BY rank DESC\n", \
   keywords=keywords)
   return results

def neo4jToMongo(article):
   return mongoTable.find_one({ "source_url" : article['url'] })

def mongoToNeo4j(article):
   return neoDriver.session().run( "MATCH (a:Article { link : $link }) RETURN A LIMIT 1", link=article['source_url'])


def uploadNeo():
   arts = mongoTable.find()
   for art in arts
      url = art["source_url"]
      if "mp3" not in url and "mp4" not in url:
         neoDriver.session.run("MERGE (a:Article { link : $link } )", link=url)

 
