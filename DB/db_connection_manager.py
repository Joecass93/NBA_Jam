import MySQLdb
from os.path import expanduser
import sqlalchemy

def establish_db_connection(connection_package):

    HOME_DIR = expanduser('~')

    db_info = {}
    with open(HOME_DIR + '/Documents/nba_db_info.txt') as f:
        for line in f:
            (k, v) = line.split()
            db_info[str(k)] = str(v)

    if connection_package == 'sqlalchemy':

        engine = sqlalchemy.create_engine('mysql://' + db_info['db_user'] + ':' + db_info['db_pw'] +
            '@' + db_info['db_address'] + ':' + db_info['port'] + '/nba_master', encoding='utf-8')

        return engine
    elif connection_package == 'sqlalchemylatin':

        engine = sqlalchemy.create_engine('mysql://' + db_info['db_user'] + ':' + db_info['db_pw'] +
            '@' + db_info['db_address'] + ':' + db_info['port'] + '/nba_master?charset=utf8')

        return engine

    else:

        raise ValueError('Invalid connection package - ' + str(connection_package) )


if __name__ == '__main__':
	main()
