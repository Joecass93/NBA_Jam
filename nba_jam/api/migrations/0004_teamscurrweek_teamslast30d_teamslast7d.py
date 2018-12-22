# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-11-17 01:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_currweek_last30d_last7d'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeamsCurrWeek',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team', models.CharField(max_length=50)),
                ('team_abbrv', models.CharField(max_length=3)),
                ('team_id', models.CharField(max_length=15)),
                ('games', models.FloatField()),
                ('games_picked', models.FloatField()),
                ('wins', models.FloatField()),
                ('losses', models.FloatField()),
                ('total_bb_picked', models.FloatField()),
                ('best_bet_wins', models.FloatField()),
                ('date_range', models.CharField(max_length=100)),
                ('fav_games', models.FloatField()),
                ('cover_games', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='TeamsLast30d',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team', models.CharField(max_length=50)),
                ('team_abbrv', models.CharField(max_length=3)),
                ('team_id', models.CharField(max_length=15)),
                ('games', models.FloatField()),
                ('games_picked', models.FloatField()),
                ('wins', models.FloatField()),
                ('losses', models.FloatField()),
                ('total_bb_picked', models.FloatField()),
                ('best_bet_wins', models.FloatField()),
                ('date_range', models.CharField(max_length=100)),
                ('fav_games', models.FloatField()),
                ('cover_games', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='TeamsLast7d',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team', models.CharField(max_length=50)),
                ('team_abbrv', models.CharField(max_length=3)),
                ('team_id', models.CharField(max_length=15)),
                ('games', models.FloatField()),
                ('games_picked', models.FloatField()),
                ('wins', models.FloatField()),
                ('losses', models.FloatField()),
                ('total_bb_picked', models.FloatField()),
                ('best_bet_wins', models.FloatField()),
                ('date_range', models.CharField(max_length=100)),
                ('fav_games', models.FloatField()),
                ('cover_games', models.FloatField()),
            ],
        ),
    ]