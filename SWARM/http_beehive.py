## Test HTTP communication with beehive
import requests
import json
import base64

example_string = "Hello!"

encoded_str = base64.b64encode(example_string.encode('utf-8'))

login = {"username": "kirkmartinez", "password": "LarypNECeSiVE"}

headers = {"Content-Type": "application/x-www-form-urlencoded"}

login_url="https://bumblebee.hive.swarm.space/hive/login"
messages_url ="https://bumblebee.hive.swarm.space/hive/api/v1\
/messages"
count_url = "https://bumblebee.hive.swarm.space/hive/api/v1\
/messages/count"

data_body= {
"deviceType": 1,
"deviceId": 8700,
"userApplicationId": 2317,
"data": encoded_str
}

session = requests.Session()

response = session.post(login_url, headers = headers, data = login)
#print(response.text)
print(session.cookies.get_dict())

cookies = session.cookies.get_dict()
#print(cookies)

response1 = session.get(count_url)#, cookies= cookies)

print(response1.json())

response2 = session.post(messages_url, data = data_body)

print(response2.json())