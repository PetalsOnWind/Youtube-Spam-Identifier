# Usage example:
# python comments.py --videoid='<video_id>'

import httplib2
import os
import sys

from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:
   %s
with information from the APIs Console
https://console.developers.google.com

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

# Authorize the request and store authorization credentials.


def get_authenticated_service(args):
    flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_READ_WRITE_SSL_SCOPE,
                                   message=MISSING_CLIENT_SECRETS_MESSAGE)

    storage = Storage("%s-oauth2.json" % sys.argv[0])
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    with open("youtube-v3-discoverydocument.json", "r") as f:
        doc = f.read()
        return build_from_document(doc, http=credentials.authorize(httplib2.Http()))


# Call the API's commentThreads.list method to list the existing comment threads.
def get_comment_threads(youtube, video_id):
    results = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        textFormat="plainText",
        maxResults="100"
    ).execute()

    for item in results["items"]:
        comment = item["snippet"]["topLevelComment"]
        author = comment["snippet"]["authorDisplayName"]
        text = comment["snippet"]["textDisplay"]
        print("Comment by %s: %s" % (author, text))

        with open(f'{video_id}_comments.csv', "a") as file:
            file.write(author + ',' + text)
            file.write('\n')

    return results["items"]


# Call the API's comments.list method to list the existing comment replies.
def get_comments(youtube, parent_id):
    results = youtube.comments().list(
        part="snippet",
        parentId=parent_id,
        textFormat="plainText"
    ).execute()

    for item in results["items"]:
        author = item["snippet"]["authorDisplayName"]
        text = item["snippet"]["textDisplay"]
        print("Comment by %s: %s" % (author, text))

    return results["items"]


# Call the API's comments.markAsSpam method to mark an existing comment as spam.
def mark_as_spam(youtube, comment):
    youtube.comments().markAsSpam(
        id=comment["id"]
    ).execute()

    print("%s marked as spam succesfully" % (comment["id"]))


if __name__ == "__main__":
    # The "videoid" option specifies the YouTube video ID that uniquely
    # identifies the video for which the comment will be inserted.
    argparser.add_argument("--videoid",
                           help="Required; ID for video for which the comment will be inserted.")
    args = argparser.parse_args()

    if not args.videoid:
        exit("Please specify videoid using the --videoid= parameter.")

    youtube = get_authenticated_service(args)
    # All the available methods are used in sequence just for the sake of an example.
    try:
        video_comment_threads = get_comment_threads(youtube, args.videoid)

    except HttpError as e:
        print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
