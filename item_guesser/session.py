from riotwatcher import *
from summoner_crawler import SummonerCrawler

class Session:
    SESSION_TOKEN = 'RGAPI-7ad0a6fd-e3c0-413b-bf6a-61fb5d71b794'

    def __init__(self, token):
        self.api = LolWatcher(token, default_match_v5=True)

if __name__ == '__main__':
    session: Session = Session(Session.SESSION_TOKEN)
    
    unknown_profile = 'Unknown Profile'
    sk_friedtater = 'SK FriedTater'

    new_matches = SummonerCrawler(session, sk_friedtater)

    print(new_matches)
    print(len(list_of_visited))
    print(len(list_of_unvisited))