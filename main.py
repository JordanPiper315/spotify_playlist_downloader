import os
import shutil
import requests
from urllib.parse import urlencode
import base64
import webbrowser
import json
import spotipy
from pytube import YouTube
from spotipy.oauth2 import SpotifyClientCredentials
import csv
from selenium import webdriver
import urllib
import urllib.error
import urllib.request
import time
from colorama import Fore, Back, Style
from dotenv import load_dotenv
from googleapiclient.discovery import build
  # app tries to hit spotify api if recieves a 400 then goes through authorization else if 200 then scrapes grabs playlist and download artists and songs from playlist. Puts those in a csv. Then hit youtube api to find video and get url of video then hit pytube to download video in mp3 format.

  # updates to be made - labor day weekend then submit for cs course
    # get a try except for block for spotify auth, try to hit the api, if you hit 400 go through auth process: hit accounts spotify auth with auth headers which open localhost, get the code that is the end of the url prefixed with code=. Use that code to get the api token then use the api token to hit the endpoint. Create an automated flow.
    # The other issue is that the google youtube api only allows for 100 hits a day therefore i want to create files with 100 song titles in them postfixed with 1 2 3 etc then when it finishes it says 1 is finished and autofills to 2 for downloading next time it is hit with the api
    # also figure out how to move files to folder post download
    # testing

load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

def main():
  with open('./songsTitlesAndArtists.csv') as file_obj:
    reader_obj = csv.reader(file_obj)
    for row in reader_obj:
      print('csv row',row[0], row[1])
      download_video_as_mp3(row[0], row[1])

def download_video_as_mp3(song_name, artist_name):
  youtube = build('youtube', 'v3', developerKey = YOUTUBE_API_KEY)
  request = youtube.search().list(q=f'{song_name}, {artist_name}, Lyrics',part='snippet',type='video',maxResults=1)
  res = request.execute()
  for item in res['items']:
    print('youtube title',item['snippet']['title'])
    print(item['id']['videoId'], item['snippet']['channelTitle'])
    url = (f"youtube.com/watch?v={item['id']['videoId']}&ab_channel={item['snippet']['channelTitle']}")
  download_mp3_from_youtube(url)

def download_mp3_from_youtube(url):
  url = url
  try:
    video = YouTube(url)
    stream = video.streams.filter(only_audio=True).first()
    audio_file = stream.download(filename=f"{video.title}.mp3")
    print(Fore.BLUE + 'The video is downloaded in MP3')
    # shutil.move(audio_file, "./downloaded_songs")
    # print(Fore.GREEN + 'This file is moved into folder')
    print(Style.RESET_ALL)
    time.sleep(3)
  except:
    print('Unable to fetch video info. Please check the video URL or your network connection.')


def spotify_auth():
  auth_headers = {
    "client_id": SPOTIPY_CLIENT_ID,
    "response_type": "code",
    "redirect_uri": "http://localhost:7777/callback",
    "scope": "user-library-read"
  }
  webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))
  driver = webdriver.Chrome()
  
  code = driver.current_url
  print(code)

  encoded_credentials = base64.b64encode(SPOTIPY_CLIENT_ID.encode() + b':' + SPOTIPY_CLIENT_SECRET.encode()).decode("utf-8")

  token_headers = {
    "Authorization": "Basic " + encoded_credentials,
    "Content-Type": "application/x-www-form-urlencoded"
  }
  token_data = {
    "grant_type": "authorization_code",
    "code": code,
    "redirect_uri": "http://localhost:7777/callback"
  }
  r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)

  token = r.json()["access_token"]

  user_headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json"
  }

  user_params = {
    "limit": 50,
    "offset": 50
  }
  return user_params, user_headers

def spotify_request(user_params, user_headers):
  user_tracks_response = requests.get("https://api.spotify.com/v1/playlists/6t1WrMPiSAB5jt0BdtKfum/tracks?offset=0&limit=50", params=user_params, headers=user_headers)
  json_data = user_tracks_response.json()
  # print(json_data)
  offset_num = 0
  while (json_data['next']) != None:
    user_tracks_response = requests.get(f"https://api.spotify.com/v1/playlists/6t1WrMPiSAB5jt0BdtKfum/tracks?offset={offset_num}&limit=50", params=user_params, headers=user_headers)
    json_data = user_tracks_response.json()
    # print(json_data)
    list_of_tracks = json_data['items']
    offset_num = offset_num + 50
    field_names = ['Song Name', 'Artist Name']
    for i, track in enumerate(list_of_tracks):
      artist = track['track']['artists'][0]['name']
      song_name = track['track']['name']
      with open('songsTitlesAndArtists.csv', 'a') as csv_file:
        dict = {"Song Name": song_name, "Artist Name": artist}
        dict_obj = csv.DictWriter(csv_file, fieldnames=field_names)
        dict_obj.writerow(dict)
        # print(i, song_name, artist)

  # print(user_tracks_response.json())
  json_object = json.dumps(user_tracks_response.json(), indent=4)

  with open("songs.json", "w") as outfile:
    outfile.write(json_object)

if __name__ == '__main__':
  main()
