import requests
import json


base_address = "http://localhost:6767"
#FIST REQUEST

params = {'id': 325483006, 'year': 2003}
response = requests.get(base_address + '/test_get_method', params=params)
print(response.text)
response_text = response.text

#SECOND REQUEST

request_json = {'id': 325483006, 'year': 2003, 'requestId':str(response_text)}
response = requests.post(base_address + '/test_post_method', json=request_json)
print(response.text)

#THIRD REQUEST

new_id = (325483006 - 123503) % 92
new_year = (2003 + 123) % 45
request_json = {'id': new_id, 'year': new_year}
response_dict = json.loads(response.text)
mess = response_dict["message"]
params = {'id': mess}
response = requests.put(base_address + '/test_put_method', json=request_json, params=params)
print(response.text)


#FORTH REQUEST

response_dict = json.loads(response.text)
mess = response_dict["message"]
params = {'id': mess}
response = requests.delete(base_address + '/test_delete_method', params=params)
print(response.text)
