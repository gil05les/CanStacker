import requests
import time

from config import BOT_NAME

bot = BOT_NAME
token = None


def get_operator():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator"
    response = requests.get(url)
    time.sleep(1)

    if response.status_code == 200:
        data = response.json()
        return data["token"], 200
    return None, response.status_code


def post_operator(name, email):
    global token

    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator"
    response = requests.post(url, json={"name": name, "email": email})
    time.sleep(1)

    if response.status_code == 200:
        token = response.headers["Location"].split("/")[-1]
        return token, 200

    return None, response.status_code


def delete_operator(token_delete):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/operator/" + token_delete
    requests.delete(url)
    time.sleep(1)


def get_tcp_target():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/tcp"
    headers = {"Authentication": token}
    response = requests.get(url, headers=headers)
    time.sleep(1)

    if response.status_code == 200:
        d = response.json()
        return (
            d["coordinate"]["x"],
            d["coordinate"]["y"],
            d["coordinate"]["z"],
            d["rotation"]["roll"],
            d["rotation"]["pitch"],
            d["rotation"]["yaw"]
        )
    return None


def put_tcp_target(x, y, z, roll, pitch, yaw):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/tcp/target"
    headers = {"Authentication": token}

    data = {
        "target": {
            "coordinate": {"x": x, "y": y, "z": z},
            "rotation": {"roll": roll, "pitch": pitch, "yaw": yaw}
        },
        "speed": 200
    }

    print(f"Sending move: {data}")
    response = requests.put(url, headers=headers, json=data)
    print(f"Response: {response.status_code}")
    time.sleep(1)


def put_gripper(param):
    url = f"https://api.interactions.ics.unisg.ch/{bot}/gripper"
    headers = {"Authentication": token}
    requests.put(url, headers=headers, json=param)
    time.sleep(1)


def get_gripper():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/gripper"
    headers = {"Authentication": token}

    r = requests.get(url, headers=headers)
    time.sleep(1)
    if r.status_code == 200:
        return r.json()
    return None


def initialize():
    url = f"https://api.interactions.ics.unisg.ch/{bot}/initialize"
    headers = {"Authentication": token}
    requests.put(url, headers=headers)
    time.sleep(1)
