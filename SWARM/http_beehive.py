## Test HTTP communication with beehive
import requests
import json
import base64

example_string = "Hello!"

encoded_str = base64.b64encode(example_string.encode('utf-8'))

login = {"username": "user", "password": "pass"}

headers = {"Content-Type": "application/x-www-form-urlencoded"}

headers_2 = {"Content-Type": "application/json"}

login_url="https://bumblebee.hive.swarm.space/hive/login"
logout_url="https://bumblebee.hive.swarm.space/hive/logout"
messages_url ="https://bumblebee.hive.swarm.space/hive/api/v1\
/messages"
count_url = "https://bumblebee.hive.swarm.space/hive/api/v1\
/messages/count"

data_body= {
"deviceType": 1,
"deviceId": 3607, #evalkit = 3607, sparkfun m138 = 8700
"userApplicationId": 1235,
"data": encoded_str.decode()
}

session = requests.Session()

response = session.post(login_url, headers = headers, data = login)
#print(response.text)
print(session.cookies.get_dict())

cookies = session.cookies.get_dict()

#print(cookies)
#response1 = session.get(count_url)#, cookies= cookies)
#print(response1.json())

response2 = session.post(messages_url, headers= headers_2, json = data_body)

print(response2.json())

response3 = session.get(logout_url)
print(response3.text)
#print(response3.json())