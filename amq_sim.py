class Song:
     def __init__(self, id, name, artist, anime, type, difficulty, correctCount, plays):
        self.id = id
        self.name = name
        self.artist = artist
        self.anime = anime
        self.type = type
        self.difficulty = difficulty
        self.correctCount = correctCount
        self.plays = plays

import configparser

config = configparser.RawConfigParser()
config.read('config.cfg')
config_options = dict(config.items('OPTIONS'))

p1_type_stats = [0, 0, 0]
p2_type_stats = [0, 0, 0]
off_list_multipliers = [float(config_options['p1_off_list_multiplier']), float(config_options['p2_off_list_multiplier'])]

import json
import random

with open('results.txt', 'w') as file:
    file.write("")
def calc_off_list(song, player, on_list):
    if player == 1:
        type_stats = p1_type_stats
    else:
        type_stats = p2_type_stats
    song_diff = song.difficulty
    if not on_list:
        song_diff = song_diff * 0.5
    type_diff = type_stats[song.type - 1]
    chance = type_diff * song_diff / 100
    chance = chance * off_list_multipliers[player - 1]
    # print(chance, song.name, song.anime, player)
    return chance

def load_anime_dict(data, dict, player):
    type_counts = [0, 0, 0]
    type_totals = [0, 0, 0]
    for songid in data:
        entry = data[songid]
        for animeid in entry['anime']:
            anime_id_names = entry['anime'][animeid]['names']
            anime = anime_id_names['EN'] if anime_id_names['EN'] else anime_id_names['JA']
        try:
            current_entry = dict[anime]
        except KeyError:
            current_entry = []
        correct_count = 0 if entry['totalCorrectCount'] is None else int(entry['totalCorrectCount'])
        wrong_count = 0 if entry['totalWrongCount'] is None else int(entry['totalWrongCount'])
        plays = correct_count + wrong_count
        try:
            entry['type']
        except KeyError:
            entry['type'] = 1
        song = Song(songid, entry['name'], entry['artist'], anime, entry['type'], entry['globalPercent'], correct_count, plays) 
        current_entry.append(song)
        dict[anime] = current_entry
        type_counts[entry['type'] - 1] += correct_count
        type_totals[entry['type'] - 1] += plays
    for i in range(3):
        if type_totals[i] != 0:
            if player == 1:
                p1_type_stats[i] = type_counts[i] / type_totals[i]
            else:
                p2_type_stats[i] = type_counts[i] / type_totals[i]

import sys
lives = config_options['lives'] == 'True'
# read in p1 data
# for each anime in p1 make a dict
 # each anime has a dict of songs and their difficulties
with open('amq_stats-brett2.json', 'rb') as file:
    data = json.load(file)
p1_anime_dict = {}
load_anime_dict(data, p1_anime_dict, 1)

# read in p2 data
# for each anime in p2 make a dict
 # each anime has a dict of songs and their difficulties
with open('amq_stats-jarod.json', 'rb') as file:
    data = json.load(file)
p2_anime_dict = {}
load_anime_dict(data, p2_anime_dict, 2)

games = int(config_options['games'])
p1_wins = 0
p2_wins = 0
ties = 0
def build_weighted_anime_list(anime_dict):
    weighted = []
    for anime, songs in anime_dict.items():
        entries = 1 + (len(songs) // 4)
        weighted.extend([anime] * entries)
    return weighted
for game in range(games):
    # sample 100 anime from each player
    # get 100 random keys from the dicts
    p1_weighted = build_weighted_anime_list(p1_anime_dict)
    p2_weighted = build_weighted_anime_list(p2_anime_dict)
    p1_anime = random.sample(p1_weighted, 100)
    p2_anime = random.sample(p2_weighted, 100)
    anime_list = p1_anime + p2_anime
    p1_score = 0
    p2_score = 0
    p1_lives = 5
    p2_lives = 5
    songs = 20 if not lives else 100
    for song in range(songs):
        # sample a random anime
        anime = random.choice(anime_list)
        # remove anime from list
        anime_list.remove(anime)
        # get a random song from the anime
        try :
            song_selection = p1_anime_dict[anime]
        except KeyError:
            song_selection = p2_anime_dict[anime]
        counts = len(song_selection)
        random_idx = random.randint(0, counts - 1)
        try :
            p1_song = p1_anime_dict[anime][random_idx]
        except KeyError:
            p1_song = None
        try :
            p2_song = p2_anime_dict[anime][random_idx]
        except (KeyError, IndexError):
            p2_song = None
        # check if the players have that song
        if p1_song is not None: # if they do, get their percentage
            if p1_song.plays == 0:
                p1_chance = calc_off_list(p1_song, 1, True)
            else :
                p1_chance = p1_song.correctCount / p1_song.plays
        else:         # if not, do some formula using the song diff and that players guess rate based
            p1_chance = calc_off_list(p2_song, 1, False)
        if p2_song is not None: # if they do, get their percentage
            if p2_song.plays == 0:
                p2_chance = calc_off_list(p2_song, 2, True)
            else :
                p2_chance = p2_song.correctCount / p2_song.plays
        else:         # if not, do some formula using the song diff and that players guess rate based
            p2_chance = calc_off_list(p1_song, 2, False)
        # roll a dice to see if the player gets the song right
        p1_roll = random.random()
        p2_roll = random.random()
        p1_correct = False
        p2_correct = False
        if p1_roll < p1_chance:
            p1_correct = True
        if p2_roll < p2_chance:
            p2_correct = True
        if not lives:
            p1_score += p1_correct
            p2_score += p2_correct
        else:
            if p1_correct and not p2_correct:
                p2_lives -= 1
            elif p2_correct and not p1_correct:
                p1_lives -= 1
            if p1_lives == 0:
                p2_wins += 1
                break
            elif p2_lives == 0:
                p1_wins += 1
                break
        # if they do, add to their score
    # after all songs are done, check who won
    if not lives:
        if p1_score > p2_score:
            p1_wins += 1
        elif p1_score < p2_score:
            p2_wins += 1
        else:
            ties += 1
    # add the score to the results file
        results_string = f"Game {game+1}: {str(p1_score)} - {str(p2_score)}\n"
    else:
        results_string = f"Game {game+1}: {str(p1_lives)} - {str(p2_lives)}\n"
    with open('results.txt', 'a') as file:
        file.write(results_string)
with open('results.txt', 'a') as file:
    results_string = f"{p1_wins}-{p2_wins}-{ties}\n"
    print(results_string)
    file.write(results_string)
        