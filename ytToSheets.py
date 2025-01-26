import os
from googleapiclient.discovery import build
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set up API Keys and configurations
YOUTUBE_API_KEY = ''
SPREADSHEET_NAME = "ytdata"
CHANNEL_HANDLE = 'indiatoday'

#service build
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# fxn to get Channel ID from the username
def get_channel_id_from_username(handle):

    request = youtube.channels().list(
        part="statistics",
        forHandle=handle
    )
    response = request.execute()
    
    # Extract channel ID
    if 'items' in response and len(response['items']) > 0:
        print("Channel ID: ", response['items'][0]['id'])       
        return response['items'][0]['id']
    else:
        raise ValueError("Channel not found")

# fxn to fetch videos from the channel using its ID
def fetch_youtube_data(channel_id):
    
    request = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        maxResults=50,
        order="date"
    )
    response = request.execute()

    video_data = []
    for item in response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            video_id = item["id"]["videoId"]
            video_title = item["snippet"]["title"]

            # Get video statistics
            stats_request = youtube.videos().list(
                part="statistics",
                id=video_id
            )
            stats_response = stats_request.execute()
            views = stats_response["items"][0]["statistics"].get("viewCount", 0)

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            video_data.append({
                "Title": video_title,
                "URL": video_url,
                "ID": video_id,
                "Views": views
            })
    return video_data

# fxn to insert data into Google Sheets
def insert_into_google_sheet(data):
    # Google Sheets setup
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    creds = ServiceAccountCredentials.from_json_keyfile_name("sheets_google.json", scope)

    client = gspread.authorize(creds)

    # Open the spreadsheet
    sheet = client.open(SPREADSHEET_NAME).sheet1

    # Insert data into the spreadsheet
    headers = ["Title", "URL", "ID", "Views"]
    sheet.append_row(headers)

    for row in data:
        sheet.append_row([row["Title"], row["URL"], row["ID"], row["Views"]])

# Main fxn
if __name__ == "__main__":
    try:
        channel_id = get_channel_id_from_username(CHANNEL_HANDLE)

        videos = fetch_youtube_data(channel_id)

        insert_into_google_sheet(videos)

        print("Data inserted successfully into Google Spreadsheet.")
    except Exception as e:
        print(f"Error: {e}")