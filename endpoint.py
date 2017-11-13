import pymongo, config, json, re
from dateutil import parser
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
import searchEndpoint
from searchEndpoint import neoDriver
app = Flask(__name__)
CORS(app)
conn = pymongo.MongoClient()[config.mongo_db]

debug = False

@app.route('/get_keywords')
def get_keywords():
    email = request.args.get("email") if request.args.get("email") else ""
    return get_keywords(email)

@app.route('/set_user')
def set_user():
    keywords = request.args.get("keywords") if request.args.get("keywords") else ""
    email = request.args.get("email") if request.args.get("email") else ""
    return set_user(email, keywords)

@app.route('/get_user')
def get_user():
    email = request.args.get("email") if request.args.get("email") else ""
    return get_user(email)

@app.route('/get_content')
def get_content():
    url = request.args.get("url") if request.args.get("url") else ""
    return get_content(url)

@app.route('/set_rating')
def set_rating():
	rating = request.args.get("rating") if request.args.get("rating") else ""
	url = request.args.get("url") if request.args.get("url") else ""
	return set_rating(rating, url)

@app.route("/")
def index():
    query = request.args.get("q") if request.args.get("q") else ""
    return get_news(query)
def listToDict(l):
   d = dict()
   for (x, y) in d:
      if x in d.keys():
         d[x].add(y)
      else:
         d[x] = list(y)
   return d  
def get_news(query):
	exit = []
	records = []
	keywords = list(query.split())
	with neoDriver.session() as session:
		records = session.run( \
			"Match (k:Keyword) WHERE k.name in $keywords " + \
			"WITH k " + \
			"MATCH (a:Article)-[h:Has]->(k) WITH a, collect(k.name) as keys,  sum(h.certainty) AS rank " + \
			"RETURN a.link AS link, keys, rank ORDER BY rank DESC LIMIT 125", keywords=keywords)
	
	neos = { record['link'] : { 'keys' : record['keys'], 'rank' : record['rank'] }  for record in records } 
	if debug:
		print('Neo4j Results')
		print(neos)
	links = list(neos.keys())
	records = list(conn[config.mongo_col].find({"link": { "$in" : links } } ))
	if debug:
		print('Mongo Results')
		print(records)
	for record in records:
		record.update(neos[record['link']])
	records = sorted(records, key=lambda x: x['rank'])
	if debug:
		print('Combined Results')
		print(records)
	#The records come back with an extra attribute 'keys', the value of which is a list of strings
	i, j, rows = 1, 1, 9
	for record in records:
		#print(record)
		img = None
		#if "media_thumbnail" in record and "url" in record["media_thumbnail"][0]:
		#	img = record["media_thumbnail"][0]["url"]
		if not img and "media_content" in record and "url" in record["media_content"][0]:
			img = record["media_content"][0]["url"]
		if not img and "links" in record and len(record["links"]) > 0:
			for link in record["links"]:
				if "image/" in link["type"]:
					img = link["href"]
		if not img and  "content" in record and len(record["content"]) > 0:
			if "value" in record["content"][0]:
				try:
					imgs = re.findall('src="(.*?)"', record["content"][0]["value"], re.DOTALL)
					if len(imgs) > 0:
						img = imgs[0]
				except:
					pass
		if not img:
			#print(json.dumps(record))
			img = "./index_files/default.png"
		published = datetime.now()
		if "published" in record:
			published = parser.parse(record['published'])
		str_published = datetime.strftime(published, "%d/%b")
		title = record["title"]
		keys = record["keys"]
		source = record["source_table"]
		if "author" in record:
			author = record["author"]
		else:
			author = ""
		titlefull = title
		if len(title) > 48:
			title = title[:48] + "..."
		exit.extend((record["_id"] + "|" + img, title, str_published, i, j, source, titlefull, author, keys))
		j += 1
		if j > rows:
			j = 1
			i += 1
	return json.dumps(exit)

def get_keywords(email):
    user = conn[config.col_users].find_one({"email": email})
    return json.dumps(user["keywords"])

def set_user(email, keywords):
    user = conn[config.col_users].find_one({"email": email})
    keys = keywords.split(",")
    for key in keys:
        if not key in user["keywords"]:
            user["keywords"].append(key)
    conn[config.col_users].save(user)
    return json.dumps(user)

def set_rating(rating, url):
	record = conn[config.mongo_col].find_one({"_id" : url})
	if not "rating" in record or record["rating"] != rating:
		conn[config.mongo_col].update({"_id" : url },{"$set" : {"rating": rating}})
	return json.dumps(record)

def get_user(email):
	user = conn[config.col_users].find_one({"email": email})
	if user:
		return json.dumps(user)
	else:
		new_user = {
			"_id": email,
			"email": email,
			"keywords": []
		}
		conn[config.col_users].save(new_user)
		return json.dumps(new_user)
	
def get_content(url):
	exit = []
	record = conn[config.mongo_col].find_one({"_id" : url})
	
	if "author" in record:
		author = record["author"]
	else: 
		author = "no author found"

	title = record["title"]
	
	if "source_name" in record:
		sourceweb = record["source_name"]
	else:
		sourceweb = "no source available"

	if "content" in record and "value" in record["content"][0]: 
		content = record["content"][0]["value"]
	else:
		if "summary" in record:
			content = record["summary"]
		else:
			content = "No content available"
			
	if "rating" in record:
		rating = record["rating"]
	else:
		rating = ""
		
	videolink = None
	if "source_content" in record:
		if record["source_content"] == "video":
			if "link" in record:
				videolink = record["link"]
	if not videolink:
		videolink = ""
	
	exit.extend((record["_id"], author, title, sourceweb, content, videolink, rating))
	
	return json.dumps(exit)

app.run(host='0.0.0.0', threaded=True, port=5000)
