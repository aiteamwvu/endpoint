from newspaper import Article
from neo4j.v1 import GraphDatabase, basic_auth
import time
from pymongo import MongoClient


neoDriver = GraphDatabase.driver("bolt://10.138.0.3:7687", auth=basic_auth("neo4j", "edupassword"))

mongoDriver = MongoClient()
mongoTable = mongoDriver["test"]["Article"]


def dbSearch(searchString):
   keywords = searchString.split(" ")
   with neoDriver.session() as session:
      results = session.run( \
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
   for art in arts:
      print(art)
      url = art["id"]
      if not '.' in url:
         url = art['link']
      print(url)
      if "mp3" not in url and "mp4" not in url and "video" not in url:
         print('Waiting on neo')
         with neoDriver.session() as session:
         	session.run("MERGE (a:Article { link : $link } )", link=url)
         print('waiting on loop')
      
   

if __name__ == '__main__':
   uploadNeo()
