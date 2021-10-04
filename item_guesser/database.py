from typing import DefaultDict
import requests, json
import os
from session import Session

class Database:
    def __init__(self, language = 'en_US', server = 'euw1', region = 'europe', champions_version = '11.16.1', item_version = '11.16.1', match_count = 0, champions = {}, items = {}, champion_items = {}, cache_path = None):
        self.champions_version = champions_version
        self.item_version = item_version
        self.language = language
        self.server = server
        self.region = region
        self.cache_path = cache_path

        self.match_count = match_count

        self.champions = champions
        self.items = items
        self.champion_items = champion_items

    # Initialize a database using the list of champions and items found on the net
    @staticmethod
    def load(session, cache_path = None):
        if cache_path is not None and len(cache_path) and os.path.exists(cache_path):
            db = Database.read(cache_path)
            db.cache_path = cache_path
            return db

        db = Database()
        db.cache_path = cache_path
        version = session.api.data_dragon.versions_for_region(db.server)
        db.champions_version = version['n']['champion']
        db.item_version = version['n']['item']

        # Get a list of itesm and champion
        champions = session.api.data_dragon.champions(db.champions_version)
        items = session.api.data_dragon.items(db.item_version)

        def filter_items(item):
            item = item[1]
            is_leaf = 'into' not in item or len(item['into']) == 0
            tags = item['tags']
            is_consumable = 'Consumable' in tags or 'Jungle' in tags or 'Trinket' in tags
            return is_leaf and not is_consumable

        db.champions = dict(map(lambda v: (v['key'], {'name': v['name'], 'game_count': 0}), champions['data'].values()))

        allowed_items = filter(filter_items, items['data'].items())
        db.items = dict(map(lambda kv: (kv[0], {'name': kv[1]['name']}), allowed_items))
        return db

    # Write the state of the database to a file
    def write(self, p):
        with open(p, 'w') as f:
            json.dump(self.__dict__, f)

    # Read the state of the database from a file
    @staticmethod
    def read(p, cache = None):
        db = None
        with open(p, 'r') as f:
            db = json.load(f)
        db['cache_path'] = cache
        return Database(**db)

    # Save the state of the file to the cach location
    def save(self, path = None):
        if path == None:
            if self.cache_path is not None and len(self.cache_path):
                self.write(self.cache_path)
            else:
                print("Failed to autosave database as no cache path was given")
        else:
            self.write(path)

    # Indicate one more match have been added to the database
    def inc_match_count(self):
        self.match_count = self.match_count + 1

    # Register an item as having been used
    # This will fail if the champion or item is not valid according to the list of champions and items
    def add_champion_item(self, champion, item, order):
        if champion not in self.champions:
            raise LookupError('Unknown champion with id {}'.format(champion))
        if item not in self.items:
            raise LookupError('Unknown item with id {}'.format(item))
        if order < 0:
            raise LookupError('Order was less then zero, recieved {}'.format(order))

        champion_stats = self.champion_items.setdefault(champion, {})
        item_stats = champion_stats.setdefault(item, {})
        item_stats[order] = item_stats.get(order, 0) + 1

        self.champions[champion]['game_count'] = self.champions[champion]['game_count'] + 1

    def __repr__(self) -> str:
        return str((len(self.champions), len(self.items), len(self.champion_items)))

    def __enter__(self):
        return self

    # Make sure the results are saved in case of a crash
    def __exit__(self, exc_type, exc_value, traceback):
        self.save()

class LookupError(KeyError):
    def __init__(self, *args, **kwargs):
        super(LookupError, self).__init__(*args, **kwargs)

if __name__ == '__main__':
    session: Session = Session(Session.SESSION_TOKEN)
    cache_path = 'data/testDb.db'
    with Database.load(session, cache=cache_path) as db:
        db.add_champion_item('25', '1018', 0)
        pass
