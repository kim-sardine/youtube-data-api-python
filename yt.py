import httplib2
import os
import time
import sys

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


class Youtube:
    def __init__(self):
        self.load_client()

    def load_client(self):
        CLIENT_SECRETS_FILE = "client_secrets.json"

        # This variable defines a message to display if the CLIENT_SECRETS_FILE is
        # missing.
        MISSING_CLIENT_SECRETS_MESSAGE = """
        WARNING: Please configure OAuth 2.0

        To make this sample run you will need to populate the client_secrets.json file
        found at:

        %s

        with information from the API Console
        https://console.developers.google.com/

        For more information about the client_secrets.json file format, please visit:
        https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
        """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                        CLIENT_SECRETS_FILE))

        # This OAuth 2.0 access scope allows for read-only access to the authenticated
        # user's account, but not other types of account access.
        YOUTUBE_READ_WRITE_SCOPE  = "https://www.googleapis.com/auth/youtube"
        YOUTUBE_API_SERVICE_NAME = "youtube"
        YOUTUBE_API_VERSION = "v3"

        flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
            message=MISSING_CLIENT_SECRETS_MESSAGE,
            scope=YOUTUBE_READ_WRITE_SCOPE )

        storage = Storage("%s-oauth2.json" % sys.argv[0])
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            flags = argparser.parse_args()
            credentials = run_flow(flow, storage, flags)

        youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
            http=credentials.authorize(httplib2.Http()))

        self.client = youtube

    def list_videoIds(self, playlistId: str) -> list:
        videoIds = []

        request = self.client.playlistItems().list(
            playlistId=playlistId,
            part="snippet",
            maxResults=50,
        )
        
        while request:
            response = request.execute()
            items = response['items']
            videoIds.extend([v['snippet']['resourceId']['videoId'] for v in items])
            request = self.client.playlistItems().list_next(request, response)

        return videoIds

    def list_playlists(self) -> list:
        playlists = []

        request = self.client.playlists().list(
            part="snippet",
            mine=True,
            maxResults=50,
        )
        
        while request:
            response = request.execute()
            items = response['items']
            playlists.extend([
                {
                    "id": item['id'],
                    "title": item['snippet']['title']
                } for item in items
            ])
            request = self.client.playlistItems().list_next(request, response)

        return playlists
    
    def delete_all_playlists(self):
        playlists = self.list_playlists()
        for playlist in playlists:
            response = self.client.playlists().delete(
                id=playlist['id']
            ).execute()

    def craete_playlist(self, title, videoIds) -> str:
        response = self.client.playlists().insert(
            part="snippet,status",
            body=dict(
                snippet=dict(
                    title=title,
                ),
                status=dict(
                    privacyStatus="public"
                )
            )
        ).execute()
        playlist_id = response["id"]

        for videoId in videoIds:
            response = self.client.playlistItems().insert(
                part="snippet,contentDetails",
                body=dict(
                    snippet=dict(
                        playlistId=playlist_id,
                        resourceId=dict(
                            kind="youtube#video",
                            videoId=videoId
                        )
                    ),
                )
            ).execute()
            # time.sleep(2) # Quota limit..

        return playlist_id
