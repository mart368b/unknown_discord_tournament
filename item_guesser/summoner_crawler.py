class Item:
    def __init__(self, id, timestamp) -> None:
        self.id = id
        self.created_time = timestamp
        self.removed_time = -1

    def __repr__(self) -> str:
        return str((self.id, self.created_time, self.removed_time))

class SummonerCrawler:
    def __init__(self, session, db, root_user: str) -> None:
        me = session.api.summoner.by_name(db.server, root_user)

        self.db = db

        self.list_of_visited_summoners = set()
        self.list_of_unvisited_summoners = set()
        self.list_of_matches = set()
        self.list_of_unprocessed_matches = set()

        self.process_summoner(session, me['puuid'], True)

        print('Current matches: {}'.format(self.list_of_matches))
        print('Visited: {}, Unvisited: {}'.format(len(self.list_of_visited_summoners), len(self.list_of_unvisited_summoners)))

    def run(self, session, process_count, summoner_limit, auto_save_rate):

        processed = 0
        while True:

            to_visit = self.list_of_unvisited_summoners.pop()
            self.process_summoner(session, to_visit, add_participants = len(self.list_of_unvisited_summoners) < summoner_limit)
            print('Visited: {}, Unvisited: {}'.format(len(self.list_of_visited_summoners), len(self.list_of_unvisited_summoners)))

            while self.list_of_unprocessed_matches:
                match = self.list_of_unprocessed_matches.pop()
                print('Working on {}, {} is remaining'.format(match, len(self.list_of_unprocessed_matches)))
                self.process_match(session, match)
                processed += 1
                if processed % auto_save_rate == (auto_save_rate - 1):
                    self.db.save()

                if processed > process_count:
                    return

    @staticmethod
    def __flatten__(a):
        return [item for sublist in a for item in sublist]

    BOUGHT_ITEM = 'ITEM_PURCHASED'
    SOLD_ITEM = 'ITEM_SOLD'
    UNDO_ITEM = 'ITEM_UNDO'

    event_filter = [
        BOUGHT_ITEM,
        SOLD_ITEM,
        UNDO_ITEM
    ]

    def process_match(self, session, match_id):
        # Get information about the participants
        match_info = session.api.match.by_id(self.db.region, match_id)
        participants = match_info['metadata']['participants']
        champions = map(lambda p: (p['championId'], p['championName']),match_info['info']['participants'])
        participants_champions = dict(zip(participants, champions))

        # Get information about the items the participants bought
        match = session.api.match.timeline_by_match(self.db.region, match_id)
        participants = match['metadata']['participants']
        timeline = match['info']['frames']

        final_items = [{} for _ in range(0, 10)]
        events = list(filter(lambda evt: evt['type'] in SummonerCrawler.event_filter, sorted(SummonerCrawler.__flatten__(map(lambda batch: batch['events'], timeline)), key=lambda evt: evt['timestamp'])))

        for event in events:
            participant_id = event['participantId'] - 1
            items = final_items[participant_id]
            ty = event['type']

            add_to_list = {
                SummonerCrawler.BOUGHT_ITEM: lambda evt: True,
                SummonerCrawler.SOLD_ITEM: lambda evt: False,
                SummonerCrawler.UNDO_ITEM: lambda evt: evt['beforeId'] == 0,
            }[ty](event)

            item_id = str({
                SummonerCrawler.BOUGHT_ITEM: lambda evt: evt['itemId'],
                SummonerCrawler.SOLD_ITEM: lambda evt: evt['itemId'],
                SummonerCrawler.UNDO_ITEM: lambda evt: evt['afterId'] if add_to_list else evt['beforeId'],
            }[ty](event))

            if not item_id in self.db.items:
                continue

            if add_to_list:
                if ty != SummonerCrawler.UNDO_ITEM:
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
            #print('{} bought {}'.format(champion[1], list(map(lambda item_id: self.db.items[item_id]['name'], items))))
        
    def process_summoner(self, session, id, add_participants):
        self.list_of_visited_summoners.add(id)

        matchlist = session.api.match.matchlist_by_puuid('europe', id, start = 0, count= 20)

        # timeline = session.api.match.timeline_by_match('europe', matchlist[0])
        # match = session.api.match.by_id('europe', matchlist[0])

        unvisited_matches = filter(lambda match: match not in self.list_of_matches, matchlist)

        matches_data = map(lambda id: session.api.match.by_id('europe', id), unvisited_matches)
        aram_matches = filter(lambda match: match['info']['gameMode'] == 'ARAM', matches_data)
        aram_data_matches = list(map(lambda match: {'matchId': match['metadata']['matchId'], 'participants': match['metadata']['participants']}, aram_matches))

        # there are not that many participants, so we need more
        if add_participants:
            match_participants = map(lambda match: match['participants'], aram_data_matches)
            for participants in match_participants:
                for participant in participants:
                    if participant not in self.list_of_visited_summoners and participant not in self.list_of_unvisited_summoners:
                        self.list_of_unvisited_summoners.add(participant)

        new_matches = list(map(lambda match: match['matchId'], aram_data_matches))
        self.list_of_matches.update(new_matches)
        for match in new_matches:
            self.list_of_unprocessed_matches.add(match)