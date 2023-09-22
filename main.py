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
import sys
import urllib
import urllib.error
import urllib.request
import time
from colorama import Fore, Back, Style
from dotenv import load_dotenv
from googleapiclient.discovery import build
    # also figure out how to move files to folder post download
    # testing
    # add try except to spotify request, look up how to check for chached access token, try except for access token and keep for auth code
    # add check if songs and titles csv has songs if not empty just run download
    # maybe create flow asking to download songs in playlist or import spotify music

load_dotenv()
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CODE = os.getenv("BROWSER_CODE")

def main():
  # spotify_auth()
  while True:
    with open ('songsToDownload1.txt', 'r', encoding='utf-8') as file:
      data = file.readlines()
      download_video_as_mp3(data[0])

    data[0] = ''

    with open('songsToDownload1.txt', 'w', encoding='utf-8') as file:
      file.writelines(data)
  
  # with open('./songsTitlesAndArtists1.csv') as file_obj:
  #   reader_obj = csv.reader(file_obj)
  #   for row in reader_obj:
  #     print('csv row',row[0], row[1])
      # download_video_as_mp3(row[0], row[1])

def download_video_as_mp3(input):
  youtube = build('youtube', 'v3', developerKey = YOUTUBE_API_KEY)
  request = youtube.search().list(q=f'{input}, Lyrics',part='snippet',type='video',maxResults=1)
  res = request.execute()
  for item in res['items']:
    print('youtube title',item['snippet']['title'])
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
  encoded_credentials = base64.b64encode(SPOTIPY_CLIENT_ID.encode() + b':' + SPOTIPY_CLIENT_SECRET.encode()).decode("utf-8")

  token_headers = {
    "Authorization": "Basic " + encoded_credentials,
    "Content-Type": "application/x-www-form-urlencoded"
  }
  token_data = {
    "grant_type": "authorization_code",
    "code": CODE,
    "redirect_uri": "http://localhost:7777/callback"
  }

  try:
    r = requests.post("https://accounts.spotify.com/api/token", data=token_data, headers=token_headers)
    token = r.json()["access_token"]
    print(token)
  except KeyError:
    print('Need new authorization code. Copy URL after copy= and paste as authorization code variable.')
    webbrowser.open("https://accounts.spotify.com/authorize?" + urlencode(auth_headers))
    sys.exit()

  user_headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json"
  }
  user_params = {
    "limit": 50,
    "offset": 50
  }
  spotify_request(user_params, user_headers)

def spotify_request(user_params, user_headers):
  user_playlist = input('Paste URL of Playlist: ')
  user_tracks_response = requests.get(f"https://api.spotify.com/v1/playlists/{user_playlist}/tracks?offset=0&limit=50", params=user_params, headers=user_headers)
  json_data = user_tracks_response.json()
  offset_num = 0
  while (json_data['next']) != None:
    user_tracks_response = requests.get(f"https://api.spotify.com/v1/playlists/{user_playlist}/tracks?offset={offset_num}&limit=50", params=user_params, headers=user_headers)
    json_data = user_tracks_response.json()
    list_of_tracks = json_data['items']
    offset_num = offset_num + 50
    field_names = ['Song Name', 'Artist Name']
    for i, track in enumerate(list_of_tracks):
      artist = track['track']['artists'][0]['name']
      song_name = track['track']['name']
      with open('songsTitlesAndArtists1.csv', 'a') as csv_file:
        dict = {"Song Name": song_name, "Artist Name": artist}
        dict_obj = csv.DictWriter(csv_file, fieldnames=field_names)
        dict_obj.writerow(dict)

  json_object = json.dumps(user_tracks_response.json(), indent=4)

if __name__ == '__main__':
  main()
