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
        print('User: ', r, ' Rank-W-L: ', ranks[r][0], ranks[r][1], ranks[r][2])


if __name__ == '__main__':
    test_ranking_method()