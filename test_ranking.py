import pickle
import butterflyrank

_dbfile = '/Users/RobSchneider/Downloads/foosdb.pickle'
#_dbfile = 'foosdb.pickle'


def test_ranking_method():
    try:
        _dbhandle = pickle.load(open(_dbfile))
    except:
        raise ValueError("Unable to load database")

    ranks = butterflyrank.get_rankings(_dbhandle['matches'].values())

    for r in ranks:
        print(r, ranks[r])


if __name__ == '__main__':
    test_ranking_method()