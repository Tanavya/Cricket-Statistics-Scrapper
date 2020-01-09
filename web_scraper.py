from bs4 import BeautifulSoup
import requests
import pandas as pd
from pprint import pprint

page_dir = 'http://stats.espncricinfo.com'
start_link = "http://www.espncricinfo.com/ci/content/player/index.html"
start_year = 1971
player_runs = {}
player_cumulative_runs = {}
player_id = {} #maps player name to id(s)
player_name = {} #maps player id to name
duplicates = [] #just to see players that have same names and players that have played for different teams

def get_player_name(id):
    link = "http://www.espncricinfo.com/australia/content/player/%s.html" % id  # this link has data for all innings of this player
    response = requests.get(link, timeout=5)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.find("div", attrs = {"class" : "ciPlayernametxt"}).h1.text.strip()

def get_player_full_name(id):
    #this is to be used for cases when two different players with same names, like Raqibul Hasan, appear
    link = "http://www.espncricinfo.com/australia/content/player/%s.html" % id  # this link has data for all innings of this player
    response = requests.get(link, timeout=5)
    soup = BeautifulSoup(response.content, "html.parser")
    return soup.find("p", attrs = {"class" : "ciPlayerinformationtxt"}).span.text


def scrape_player_data(name, id):
    link = "http://stats.espncricinfo.com/ci/engine/player/%s.html?class=2;template=results;type=batting;view=innings" % id  # this link has data for all innings of this player
    response = requests.get(link, timeout=5)
    soup = BeautifulSoup(response.content, "html.parser")
    name = get_player_name(
        id)  # NOT necessary since I can use original name variable, but first and middle name are initials so I use this.
    print(name)
    table = soup.findAll("table")[3]
    assert (table.caption.text == 'Innings by innings list')

    player_id.setdefault(name, [])
    player_id[name].append(id)
    player_name[id] = name

    if len(player_id[name]) > 1:
        duplicates.append(name)
        player_name[player_id[name][-2]] = get_player_full_name(player_id[name][-2])
        player_name[id] = get_player_full_name(id)
        name = player_name[id]
        print("duplicate found:", name)

    player_runs.setdefault(id, [0 for i in range(1971,
                                                 2020)])  # some players like Luke Ronchi have played for more than one country so we must be sure not to reset their count

    for innings in table.tbody.findAll("tr"):
        tds = innings.findAll("td")
        runs = tds[0].text.replace("*", "")
        if runs.isdigit():
            year = int(tds[12].text.split(" ")[-1])
            player_runs[id][year - 1971] += int(runs)


def scrape_by_country(id):
    link = "http://www.espncricinfo.com/ci/content/player/caps.html?country=%s;class=2" % id
    response = requests.get(link, timeout=5)
    soup = BeautifulSoup(response.content, "html.parser")
    # I try to get the name and id for every player that has played for this country
    for tag in soup.find("div", attrs={"class": "ciPlayerbycapstable"}).findAll("li", attrs={"class": "ciPlayername"}):
        player_id = tag.a["href"].split("/")[-1][:-5]
        name = tag.text
        scrape_player_data(name, player_id)


response = requests.get(start_link, timeout=5)
soup = BeautifulSoup(response.content, "html.parser")


ids = [] #each country has a particular "id" that I try to find

for tag in soup.find("div", attrs={"class": "ciPlayersHomeCtryList"}).ul.findAll("li")[:-1]:
    link = tag.a["href"]
    id = link.split("=")[-1]
    ids.append(id)

#this finds ids of all common teams, and now I try to find ids of "other teams"

for tag in soup.find("div", attrs={"class": "ciPlayersHomeCtryList"}).findAll("option")[1:]:
    id = tag["value"]
    #print(tag)
    if id: ids.append(id)

for id in ids:
    print("Country ID:",id)
    scrape_by_country(id)

cumulative_runs_output = "Name," + ",".join([str(year) for year in range(1971, 2020)]) + "\n"
for id in player_runs:
    name = player_name[id]
    sum = 0
    prefix = []
    for year in range(1971, 2020):
        sum += player_runs[id][year-1971]
        prefix.append(sum)
    player_cumulative_runs[name] = prefix
    cumulative_runs_output += (name + "," + ",".join([str(x) for x in prefix]) + "\n")

f = open("player_cumulative_runs.csv", "w+")
f.write(cumulative_runs_output)
f.close()

f = open("player_runs.csv", "w+")
f.write("Name," + ",".join([str(year) for year in range(1971, 2020)]) + "\n")
for id in player_runs:
    name = player_name[id]
    f.write(name + "," + ",".join([str(x) for x in player_runs[id]]) + "\n")
f.close()


print(duplicates)