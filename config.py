import pygame
import os
import csv
import sys

WIDTH = 1920 // 2
HEIGHT = 1080 // 2
MAP_SIZE = 50
global_zoom = 1
background = (10, 10, 10)
darker_green = (0, 175, 0)
dark_green = (2, 48, 32)
lighter_green = (0, 200, 0)
red = (255, 0, 0)
yellow = (255, 255, 0)
purple = (148,0,211)
black = (0, 0, 0)
tinted = (0, 0, 0, 75)
very_tinted = (0, 0, 0, 200)
white = (255, 255, 255)
brown = (68,35,19)
green = (144, 238, 144)
grey = (125, 125, 125)

building_inventory = {"Wall": 75, "Town_Hall" : 1, "Cannon": 1, "Archer_Tower": 1, "Gold_Mine": 2, "Elixar_Collector": 2}
troop_inventory = {"barbarian": 15, "archer": 15, "wall_breaker": 2, "goblin": 15, "giant": 5, "balloon": 5}
og_troop_inventory = {"barbarian": 15, "archer": 15, "wall_breaker": 2, "goblin": 15, "giant": 5, "balloon": 5}


os.chdir(os.path.dirname(os.path.abspath(__file__)))

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(os.path.abspath("."), relative_path)

building_info = {}
building_info_path = resource_path('data/building_info.csv')

with open(building_info_path, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        building_info[row['name']] = row

troop_info = {}
troop_info_path = resource_path('data/troop_info.csv')

with open(troop_info_path, mode='r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        troop_info[row['troop']] = row

img_dict = {}
for building in building_info:
    path = resource_path(building_info[building]['img'])
    img_dict[building] = pygame.image.load(path)
for troop in troop_info:
    path = resource_path(troop_info[troop]['img'])
    img_dict[troop] = pygame.image.load(path)