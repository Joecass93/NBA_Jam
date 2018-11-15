from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Results(models.Model):
    game_date = models.DateField()
    game_id = models.CharField(max_length = 15)
    away_team = models.CharField(max_length = 3)
    home_team = models.CharField(max_length = 3)
    away_pts = models.FloatField()
    home_pts = models.FloatField()
    vegas_spread_str = models.CharField(max_length = 20)
    pred_spread_str = models.CharField(max_length = 20)
    pick_str = models.CharField(max_length = 20)
    team_covered = models.CharField(max_length = 3)
    team_picked = models.CharField(max_length = 3)
    result = models.CharField(max_length = 10)
    best_bet = models.CharField(max_length = 3)


class Picks(models.Model):
    game_date = models.DateField()
    rank = models.FloatField()
    game_id = models.CharField(max_length = 15)
    away_team = models.CharField(max_length = 3)
    home_team = models.CharField(max_length = 3)
    vegas_spread_str = models.CharField(max_length = 20)
    pred_spread_str = models.CharField(max_length = 20)
    pick_str = models.CharField(max_length = 20)
    best_bet = models.CharField(max_length = 3)


class Last30d(models.Model):
    total_games = models.FloatField()
    total_bestbets = models.FloatField()
    wins = models.FloatField()
    losses = models.FloatField()
    no_bets = models.FloatField()
    best_bet_wins = models.FloatField()
    date_range = models.CharField(max_length = 100)


## starts on monday
class CurrWeek(models.Model):
    total_games = models.FloatField()
    total_bestbets = models.FloatField()
    wins = models.FloatField()
    losses = models.FloatField()
    no_bets = models.FloatField()
    best_bet_wins = models.FloatField()
    date_range = models.CharField(max_length = 100)


class Last7d(models.Model):
    total_games = models.FloatField()
    total_bestbets = models.FloatField()
    wins = models.FloatField()
    losses = models.FloatField()
    no_bets = models.FloatField()
    best_bet_wins = models.FloatField()
    date_range = models.CharField(max_length = 100)

def __str__(self):
    return self
