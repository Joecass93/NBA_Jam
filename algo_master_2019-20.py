import requests

url = "https://free-nba.p.rapidapi.com/stats"

querystring = {"dates":"2019-03-01","page":"0","per_page":"25"}

headers = {
    'x-rapidapi-host': "free-nba.p.rapidapi.com",
    'x-rapidapi-key': "65923f9d14msh728e06e4472cedfp1c3959jsndd2e798035c2"
    }

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)