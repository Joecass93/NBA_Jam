## import data from results table
conn <- dbConnect(MySQL(), 
                  user = 'moneyteamadmin',
                  password = 'moneyteam2018',
                  host = 'nba-jam.c5tgdlkxq25p.us-east-2.rds.amazonaws.com',
                  dbname = 'nba_master')

## query data
algo_data <- dbGetQuery(conn, "SELECT * FROM results_table;")

## create column for pt diff ex. away wins by 7 then pt diff = -7
algo_data$final_spread = algo_data$pts_home - algo_data$pts_away

