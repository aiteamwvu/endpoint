import pymongo, config, json, re
from dateutil import parser
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
conn = pymongo.MongoClient()[config.mongo_db]

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

@app.route("/")
def index():
    query = request.args.get("q") if request.args.get("q") else ""
    return get_news(query)

def get_news(query):
	exit = []
	records = conn[config.mongo_col].find({"$or":[{"title": re.compile(query, re.IGNORECASE)}, {"content.value": re.compile(query, re.IGNORECASE)}, {"summary": re.compile(query, re.IGNORECASE)}]}).sort([('timestamp', pymongo.DESCENDING)]).limit(125)
	i, j, rows = 1, 1, 9
	for record in records:
		img = None
		if "media_thumbnail" in record and "url" in record["media_thumbnail"][0]:
			img = record["media_thumbnail"][0]["url"]
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
		source = record["source_table"]
		if "author" in record:
			author = record["author"]
		else:
			author = ""
		titlefull = title
		if len(title) > 48:
			title = title[:48] + "..."
		exit.extend((record["_id"] + "|" + img, title, str_published, i, j, source, titlefull, author))
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
		sourceweb = record["souce_name"]
	else:
		sourceweb = "no source available"

	if "content" in record and "value" in record["content"][0]: 
		content = record["content"][0]["value"]
	else:
		content = "Content not available"
	
	exit.extend((record["_id"], author, title, sourceweb, content))
	
	return json.dumps(exit)

app.run(host='0.0.0.0', threaded=True, port=5000)
