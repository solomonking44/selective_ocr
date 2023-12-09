import requests

url = 'https://app.nanonets.com/api/v2/ImageCategorization/UploadUrls/'

headers = {
    'accept': 'application/x-www-form-urlencoded'
}

data = {'modelId' : 'ceeebab1-5f48-4ce9-845e-066b81ce3d97', 'category': 'category1', 'urls': ['images/1.jpeg', 'images/2.jpeg', 'images/3.jpeg', 'images/4.jpeg', 'images/5.jpeg']}

response = requests.request('POST', url, headers=headers, auth= requests.auth.HTTPBasicAuth('78d1996a-9789-11ed-b6de-a693374d4922', ''), data=data)

print(response.text)