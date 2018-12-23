library(RMySQL)
library(e1071)

## import data from results table
conn <- dbConnect(MySQL(), 
                  user = 'moneyteamadmin',
                  password = 'moneyteam2018',
                  host = 'nba-jam.c5tgdlkxq25p.us-east-2.rds.amazonaws.com',
                  dbname = 'nba_master')

## query data
results <- dbGetQuery(conn, "SELECT * FROM final_scores")
agg_stats <- dbGetQuery(conn, "SELECT * FROM four_factors_thru")

## create column for pt diff ex. away wins by 7 then pt diff = -7
results$final_spread = results$pts_home - results$pts_away

merged <- merge(results, agg_stats, by.x = c("game_id", "home_id"), by.y = c("as_of", "TEAM_ID"), all.x = TRUE)
merged <- merge(merged, agg_stats, by.x = c("game_id", "away_id"), by.y = c("as_of","TEAM_ID"), all.x = TRUE, suffixes = c("_home", "_away"))

drops <- c("as_of_away", "as_of_home", "away_id", "home_id", "game_date", "sequence", "game_id",
           "away_team", "home_team", "pt_diff_away", "pts_home", "pts_away", "pts_total", "win_side", "win_id")
algo_data <- na.omit(merged[, !(names(merged) %in% drops)])

## lets graph
par(mfrow=c(1, 2))  # divide graph area in 2 columns
scatter.smooth(x=algo_data$EFG_PCT_home , y=algo_data$final_spread , main = "Home EFG Pct ~ Home Winning Margin")
boxplot(algo_data$final_spread)
plot(density(algo_data$final_spread), main = "Home Winning Margin Density")

## correlations
for (stat in names(algo_data)){
  stat_cor = cor(algo_data$final_spread, algo_data[[stat]])
  print(paste("Correlation between final winning margin and ", stat, " is: ", stat_cor))
}


## build ze linear model
linearMod <- lm(final_spread ~ EFG_PCT_home + FTA_RATE_home + TM_TOV_PCT_home + OREB_PCT_home, data = algo_data)
summary(linearMod)

