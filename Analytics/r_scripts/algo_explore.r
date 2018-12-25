library(RMySQL)
library(e1071)
library(data.table)
library(dplyr)
library(tidyverse)

## import data from results table
conn <- dbConnect(MySQL(), 
                  user = 'moneyteamadmin',
                  password = 'moneyteam2018',
                  host = 'nba-jam.c5tgdlkxq25p.us-east-2.rds.amazonaws.com',
                  dbname = 'nba_master')

## query data
results <- dbGetQuery(conn, "SELECT * FROM final_scores")
agg_stats <- dbGetQuery(conn, "SELECT * FROM four_factors_thru")
spreads <- dbGetQuery(conn, "SELECT date, away_team_id, home_team_id, bovada_line AS spread FROM spreads")

## create column for pt diff ex. away wins by 7 then pt diff = -7
results$final_spread = results$pts_home - results$pts_away

merged <- merge(results, agg_stats, by.x = c("game_id", "home_id"), by.y = c("as_of", "TEAM_ID"), all.x = TRUE)
merged <- merge(merged, agg_stats, by.x = c("game_id", "away_id"), by.y = c("as_of","TEAM_ID"), all.x = TRUE, suffixes = c("_home", "_away"))

test_merged = merged[merged$game_id %like% "002180", ]
train_merged = merged[!(merged$game_id %like% "002180"), ]
  
drops <- c("as_of_away", "as_of_home", "away_id", "home_id", "game_date", "sequence", "game_id",
           "away_team", "home_team", "pt_diff_away", "pts_home", "pts_away", "pts_total", "win_side", "win_id")
algo_test <- na.omit(test_merged[, !(names(test_merged) %in% drops)])
algo_train <- na.omit(train_merged[, !(names(train_merged) %in% drops)])

## lets graph
par(mfrow=c(1, 2))  # divide graph area in 2 columns
scatter.smooth(x=algo_train$EFG_PCT_home , y=algo_train$final_spread , main = "Home EFG Pct ~ Home Winning Margin")
boxplot(algo_train$final_spread)
plot(density(algo_train$final_spread), main = "Home Winning Margin Density")

## correlations
for (stat in names(algo_train)){
  stat_cor = cor(algo_train$final_spread, algo_train[[stat]])
  print(paste("Correlation between final winning margin and ", stat, " is: ", stat_cor))
}

## build ze linear model
linearMod <- lm(final_spread ~ EFG_PCT_home + FTA_RATE_home + TM_TOV_PCT_home + OREB_PCT_home + OPP_EFG_PCT_home + OPP_FTA_RATE_home + OPP_TOV_PCT_home + OPP_OREB_PCT_home + EFG_PCT_away + FTA_RATE_away + TM_TOV_PCT_away + OREB_PCT_away + OPP_EFG_PCT_away + OPP_FTA_RATE_away + OPP_TOV_PCT_away + OPP_OREB_PCT_away, data = algo_train)

## apply model to current season data
predict_curr_season <- predict(linearMod, algo_test)
test_merged <- na.omit(test_merged)
merge_predictions <- data.frame(test_merged, regression = predict(linearMod, test_merged))
summary(predict_curr_season)

## merge spreads into training data 
df <- merge(merge_predictions, spreads, by.x = c("game_date", "away_id", "home_id"), by.y = c("date", "away_team_id", "home_team_id"))
df[] <- lapply(df, as.character)
df$spread <- as.numeric(df$spread)
df$final_spread <- as.numeric(df$final_spread)
df$pred_spread <- as.numeric(df$regression)

## determine which team would have been picked, if best bet etc..
df <- select(df, pts_away, pts_home, game_id, final_spread, pred_spread, spread)
df$bet <- ifelse(df$spread > df$pred_spread, "Away", "Home")
df$winner <- ifelse(df$spread > df$final_spread, "Away", "Home")
df$best_bet <- ifelse(df$pred_spread - df$spread >= 3.5, "Y", 
                      ifelse(df$pred_spread - df$spread <= -3.5, "Y", "N"))

df$result <- ifelse(df$bet == df$winner, "Win", "Loss")
                                   
