import requests

response = requests.get('http://34.234.176.173:48/nacos/#/login')
if response.status_code == 200:
    print('ok')
else:
    print('not available')