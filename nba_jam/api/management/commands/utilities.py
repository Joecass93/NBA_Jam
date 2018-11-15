import sqlalchemy

def establish_db_connection(connection_package, db):

    if db == 'moneyteam':
        engine = sqlalchemy.create_engine('mysql://' + 'moneyteamadmin' + ':' + 'moneyteam2018' +
            '@' + 'nba-jam.c5tgdlkxq25p.us-east-2.rds.amazonaws.com' + ':' + '3306' + '/nba_master', encoding='utf-8')

        return engine
    elif db == 'nbaapi':
        engine = sqlalchemy.create_engine('mysql://' + 'nbajamadmin' + ':' + 'moneyteam2018' +
            '@' + 'aas6wo5k9lybv0.c5tgdlkxq25p.us-east-2.rds.amazonaws.com' + ':' + '3306' + '/nba_api', encoding='utf-8')

        return engine
    else:
        raise ValueError('Invalid connection package - ' + str(connection_package) )
