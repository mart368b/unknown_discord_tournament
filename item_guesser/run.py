from database import Database
from session import Session
from summoner_crawler import SummonerCrawler
import json
from riotwatcher import *

def flatten(a):
    return [item for sublist in a for item in sublist]

def filter_items(item):
    item = item[1]
    is_leaf = 'into' not in item or len(item['into']) == 0
    tags = item['tags']
    is_consumable = 'Consumable' in tags or 'Jungle' in tags or 'Trinket' in tags
    return is_leaf and not is_consumable

def allowed_item_list(session):
    item_list = session.api.data_dragon.items('11.16.1')
    return dict(map(lambda item: (item[0], item[1]['name']) , filter(filter_items, item_list['data'].items())))

BOUGHT_ITEM = 'ITEM_PURCHASED'
SOLD_ITEM = 'ITEM_SOLD'
UNDO_ITEM = 'ITEM_UNDO'

event_filter = [
    BOUGHT_ITEM,
    SOLD_ITEM,
    UNDO_ITEM
]

class Item:
    def __init__(self, id, timestamp) -> None:
        self.id = id
        self.created_time = timestamp
        self.removed_time = -1

    def __repr__(self) -> str:
        return str((self.id, self.created_time, self.removed_time))

if __name__ == '__main__':

    session: Session = Session(Session.SESSION_TOKEN)
    db = Database.load(session, cache_path='db.json')
    db.save('db.json')

    crawler = SummonerCrawler(session, db, 'SK FriedTater')

    crawler.run(session, 6, 50, 1000)

    """
    filtered_items = allowed_item_list(session)
    match_info = session.api.match.by_id('europe', 'EUW1_5429751912')
    with open('match_info.json', 'w') as f:
        json.dump(match_info, f)
    

    participants_champions = None
    with open('match_info.json', 'r') as f:
        match_info = json.load(f)
        participants = match_info['metadata']['participants']
        champions = map(lambda p: (p['championId'], p['championName']),match_info['info']['participants'])
        participants_champions = dict(zip(participants, champions))
    print(participants_champions)

    sk_friedtater = 'SK FriedTater'
    new_matches = SummonerCrawler(session, sk_friedtater)

    cache_path = 'data/testDb.db'
    with Database.load(session, cache_path=cache_path) as db:
        db.add_champion_item('25', '1018', 0)
        pass

    

    match_info = session.api.match.timeline_by_match('europe', 'EUW1_5429751912')
    with open('match.json', 'w') as f:
        json.dump(match_info, f)
    
    
    with open('match.json', 'r') as f:
        match = json.load(f)
        participants = match['metadata']['participants']
        timeline = match['info']['frames']

        final_items = [{} for _ in range(0, 10)]
        events = list(filter(lambda evt: evt['type'] in event_filter, sorted(flatten(map(lambda batch: batch['events'], timeline)), key=lambda evt: evt['timestamp'])))

        for event in events:
            participant_id = event['participantId'] - 1
            items = final_items[participant_id]
            ty = event['type']

            add_to_list = {
                BOUGHT_ITEM: lambda evt: True,
                SOLD_ITEM: lambda evt: False,
                UNDO_ITEM: lambda evt: evt['beforeId'] == 0,
            }[ty](event)

            item_id = str({
                BOUGHT_ITEM: lambda evt: evt['itemId'],
                SOLD_ITEM: lambda evt: evt['itemId'],
                UNDO_ITEM: lambda evt: evt['afterId'] if add_to_list else evt['beforeId'],
            }[ty](event))

            if not item_id in filtered_items:
                continue

            if add_to_list:
                if ty != UNDO_ITEM:
                    items[item_id] = Item(item_id, event['timestamp'])
                else:
                    items[item_id].removed_time = -1
            else:
                if item_id in items:
                    items[item_id].removed_time = event['timestamp']

        for participant_items in zip(participants, final_items):
            participant = participant_items[0]
            items = participant_items[1]

            champion = participants_champions[participant]
            print('{} bought {}'.format(champion[1], list(map(lambda item_id: filtered_items[item_id], items))))

            """