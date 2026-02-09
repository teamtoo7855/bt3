# get bus types from cptdb
import re
import pickle
import requests
from bs4 import BeautifulSoup

def fetch_types():
    url = 'https://cptdb.ca/wiki/index.php/Coast_Mountain_Bus_Company'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('table')
    scraped = []
    conventional = tables[1]
    trolley = tables[3]
    cshuttle = tables[5]

    for conventional_data in conventional.find_all('tbody'):
        rows = conventional_data.find_all('tr')
    for row in rows:
        if len(row.find_all('td')) == 0:
            continue
        else:
            scraped.append({
                "fleet_numbers": row.find_all('td')[0].text.strip('\t\r\n').replace('\n\n', ' '),
                "year": row.find_all('td')[2].text.strip('\t\r\n').replace('\n\n', ' '),
                "manufacturer": row.find_all('td')[3].text.strip('\t\r\n').replace('\n\n', ' '),
                "model": row.find_all('td')[4].text.strip('\t\r\n').replace('\n\n', ' '),
                "aircon": row.find_all('td')[8].text.strip('\t\r\n').replace('\n\n', ' '),
            })

    for trolley_data in trolley.find_all('tbody'):
        rows = trolley_data.find_all('tr')
    for row in rows:
        if len(row.find_all('td')) == 0:
            continue
        else:
            scraped.append({
                "fleet_numbers": row.find_all('td')[0].text.strip('\t\r\n').replace('\n\n', ' '),
                "year": row.find_all('td')[2].text.strip('\t\r\n').replace('\n\n', ' '),
                "manufacturer": row.find_all('td')[3].text.strip('\t\r\n').replace('\n\n', ' '),
                "model": row.find_all('td')[4].text.strip('\t\r\n').replace('\n\n', ' '),
                "aircon": row.find_all('td')[7].text.strip('\t\r\n').replace('\n\n', ' '),
            })

    for cshuttle_data in cshuttle.find_all('tbody'):
        rows = cshuttle_data.find_all('tr')
    for row in rows:
        if len(row.find_all('td')) == 0:
            continue
        else:
            scraped.append({
                "fleet_numbers": row.find_all('td')[0].text.strip('\t\r\n').replace('\n\n', ' '),
                "year": row.find_all('td')[2].text.strip('\t\r\n').replace('\n\n', ' '),
                "manufacturer": row.find_all('td')[3].text.strip('\t\r\n').replace('\n\n', ' '),
                "model": row.find_all('td')[4].text.strip('\t\r\n').replace('\n\n', ' '),
                "aircon": row.find_all('td')[8].text.strip('\t\r\n').replace('\n\n', ' '),
            })

    for bus in scraped:
        fleet_numbers = bus['fleet_numbers']
        fleet_numbers = re.sub(r'–|-', ' ',fleet_numbers)
        fleet_numbers = re.split(',', fleet_numbers)
        fn_range = []
        for r in fleet_numbers:
            bounds = r.split()
            fn_range.append(tuple(list(map(int,bounds))))
        bus['fn_range'] = fn_range
    
    with open('types.pkl', 'wb') as f:  # open a text file
        pickle.dump(scraped, f) # serialize the list
        print("Bus type data retrieved and saved as types.pkl")

    # for testing functionality
    # bus_id = 2117
    # bus_name = "No bus found"
    # for t in processed:
    #     for r in t['ranges']:
    #         if len(r) % 2:
    #             if bus_id == r[0]:
    #                 bus_name = t['name']
    #                 break
    #             else:
    #                 continue
    #             break
    #         if bus_id in range(r[0], r[1]):
    #             bus_name = t['name']
    #             break
    # print(bus_name)