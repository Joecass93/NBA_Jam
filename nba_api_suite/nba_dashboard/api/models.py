from __future__ import unicode_literals

from django.db import models

# Create your models here.
# class Note(models.Model):
#     title = models.CharField(max_length=200)
#     body = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

class Picks(models.Model):
    game_date = models.DateField()
    game_id = models.CharField(max_length=10)
    away_team = models.CharField(max_length=3)
    home_team = models.CharField(max_length=3)
    pts_away = models.FloatField()
    pts_home = models.FloatField()
    vegas_spread_str = models.CharField(max_length = 15)
    pred_spread_str = models.CharField(max_length = 15)
    pick_str = models.CharField(max_length = 15)
    team_covered = models.CharField(max_length = 3)
    team_picked = models.CharField(max_length = 3)
    result = models.CharField(max_length = 10)
    best_bet = models.CharField(max_length = 1)


def __str__(self):
    return '%s %s'%(self.game_id, self.result)
