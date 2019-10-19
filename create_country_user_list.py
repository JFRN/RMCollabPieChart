import csv
import json
import os
import time
from collections import Counter, OrderedDict
from os import path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import requests

# Dataset filenames
d: str = path.dirname(__file__) if "__file__" in locals() else os.getcwd()
dataset_file: str = path.join(d, 'data18-10-2019-22-42.csv') # Export of Google Forms list
key_file: str = path.join(d, 'osuapikey.txt') # Literal key
country_file: str = path.join(d, 'iso3166-alpha-2.csv') # Bundled with this file hopefully
out_data_file: str = path.join(d, 'userdata.json') # Created to avoid fetching user info repeatedly
figure_file: str = path.join(d, 'Figure_1.png')

# Relevant dataset columns
AVATAR_OPTION: int = 1
OSU_USERNAME: int = 2

COUNTRY_NAME: int = 0
COUNTRY_CODE: int = 1

def get_file_as_string(filename: str) -> str:
    with open(filename) as file:
        return file.read().replace('\n', '')

def get_countries(filename: str) -> Dict[str, str]:
    with open(filename, encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        next(reader) # skip header
        return {rows[COUNTRY_CODE]: rows[COUNTRY_NAME] for rows in reader}

def read_dataset(filename: str) -> Dict[str, str]:
    with open(filename, encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        next(reader) # skip header
        return {rows[OSU_USERNAME]: rows[AVATAR_OPTION] for rows in reader}

def query_user_info(username: str) -> Any:
    payload = {'k': OSU_API_KEY, 'u': username}
    r = requests.get('https://osu.ppy.sh/api/get_user', params=payload)

    if r.status_code != 200:
        print(f'User {username} did not return HTTP 200')
        return {}

    try:
        testAssignment = r.json()
    except ValueError:
        return {}

    if r.json():
        return r.json()[0]

    return {}

def query_users(users: List[str]) -> Dict[str, Dict[str, str]]:
    all_users: Dict[str, Dict[str, str]] = {}
    count: int = 0
    for user in users:
        # osu! API rate limit is 1200 per minute
        # so we need to stay on the low
        if count % 600 == 0 and count != 0:
            print('Sleeping one minute...')
            time.sleep(60)
        print(f'Processing {user}...')
        user_info = query_user_info(user)
        all_users[user] = user_info
        count = count + 1
    return all_users

def write_dict_to_json(data: Dict, filename: str) -> None:
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def read_dict_from_json(filename: str) -> Dict:
    with open(filename, encoding='utf-8') as file:
        return json.load(file)

def remove_empty_values(data: Dict) -> Dict:
    temp_data = dict(data)
    for k, v in data.items():
        if v == {}:
            temp_data.pop(k, None)
    return temp_data

# API Key
OSU_API_KEY: str = get_file_as_string(key_file)

# 2-digit code to country name equivalency
COUNTRIES: Dict[str, str] = get_countries(country_file)

#df = read_dataset(dataset_file)
#full_users = query_users([*df])

#write_dict_to_json(full_users, out_data_file)

full_users = read_dict_from_json(out_data_file)

# Remove invalid users
full_users = remove_empty_values(full_users)

user_countries: Dict[str, str] = {}
for user, info in full_users.items():
    user_countries[user] = COUNTRIES[info["country"]]

counts = Counter(user_countries.values())
counts = OrderedDict(counts.most_common()) # sort countries and convert to dict

COUNTRIES_TO_SHOW_MIN_PERCENT: float = 0.7
PERCENTAGES_TO_SHOW_MIN: float = 2.0

percents = [i / len(user_countries) * 100.0 for i in counts.values()]
legend_labels = [f'{i} - {j:.2f}%' for i, j in zip(counts.keys(), percents)]
pie_labels = [f'{i}' if j > COUNTRIES_TO_SHOW_MIN_PERCENT else '' for i, j in zip(counts.keys(), percents)]

def custom_autopct(pct):
    return f'{pct:.2f}%' if pct > PERCENTAGES_TO_SHOW_MIN else ''

patches, texts, _ = plt.pie(counts.values(), labels=pie_labels, autopct=custom_autopct, startangle=90)

plt.legend(patches, legend_labels, bbox_to_anchor=(1.5, 1.5), loc=2, title="Participating countries", fontsize = 6)
plt.axis('equal')
plt.show()
#plt.savefig(figure_file, dpi=400, bbox_inches='tight')
