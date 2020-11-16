import urllib.request
import json

url = 'https://data.nsw.gov.au/data/api/3/action/datastore_search?resource_id=945c6204-272a-4cad-8e33-dde791f5059a'
base_url = 'https://data.nsw.gov.au/data'

records = []
link = '/api/3/action/datastore_search?resource_id=945c6204-272a-4cad-8e33-dde791f5059a'
i = 0
while link and i < 5:
    url = base_url + link
    with urllib.request.urlopen(url) as response:
        print(url)
        link = None
        i += 1
        content = json.loads(response.read().decode('utf-8'))
        result = content.get('result', None)
        if result:
            records.append(result['records'])
            links = result.get('_links', None)
            if links:
                link = links.get('next', None)

print(json.dumps(records, indent=4))


#print(json.dumps(content['result']['records'], indent=4))
#print(json.dumps(content, indent=4))
#print(json.dumps(content['result']['_links'], indent=4))
