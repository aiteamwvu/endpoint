import pymongo, config, json, re
from dateutil import parser
from datetime import datetime
from flask import Flask, request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
conn = pymongo.MongoClient()[config.mongo_db][config.mongo_col]

@app.route('ui')
def ui():
    return app.send_static_file('/ui/index.html')

@app.route("/")
def index():
    query = request.args.get("q") if request.args.get("q") else ""
    return get_news(query)

def get_news(query):
	exit = []
	records = conn.find({"$or":[{"title": re.compile(query, re.IGNORECASE)}, {"content.value": re.compile(query, re.IGNORECASE)}, {"summary": re.compile(query, re.IGNORECASE)}]}).sort([('timestamp', pymongo.DESCENDING)]).limit(125)
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
				imgs = re.findall('src="(.*?)"', record["content"][0]["value"], re.DOTALL)
				if len(imgs) > 0:
					img = imgs[0]
		if not img:
			#print(json.dumps(record))
			img = "./index_files/default.png"
		published = datetime.now()
		if "published" in record:
			published = parser.parse(record['published'])
		str_published = datetime.strftime(published, "%d/%b")
		title = record["title"]
		source = record["source_table"]
		if len(title) > 48:
			title = title[:48] + "..."
		exit.extend((record["_id"] + "|" + img, title, str_published, i, j, source))
		j += 1
		if j > rows:
			j = 1
			i += 1
	return json.dumps(exit)

app.run(host='0.0.0.0', threaded=True)
