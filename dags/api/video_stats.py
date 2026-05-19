import requests
import json
import os
from datetime import date
from airflow.decorators import task


API_KEY = os.getenv("API_KEY")
CHANNEL_HANDLE = os.getenv("CHANNEL_HANDLE") 
maxResults = 50

@task 
def get_playlist_id():
    try:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={CHANNEL_HANDLE}&key={API_KEY}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data.get("items"):
            raise ValueError(f"No channel found with ID: {CHANNEL_HANDLE}. Check your API_KEY and CHANNEL_ID.")

        channel_items = data["items"][0]
        channel_playlist = channel_items["contentDetails"]["relatedPlaylists"]["uploads"]
        
        print(f"Playlist ID Found: {channel_playlist}")
        return channel_playlist
    
    except Exception as e:
        print(f"Error fetching channel: {e}")
        raise e

@task 
def get_video_ids(playlist_id):
  
    if not playlist_id:
        raise ValueError("playlist_id is empty or None")
        
    video_ids = []
    pageToken = None 

    try:
        while True:
            url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults={maxResults}&playlistId={playlist_id}&key={API_KEY}"
            
            if pageToken:
                url += f"&pageToken={pageToken}"
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                v_id = item['contentDetails']['videoId']
                video_ids.append(v_id)
            
            pageToken = data.get('nextPageToken')
            if not pageToken:
                break
                
        print(f"Total Video IDs fetched: {len(video_ids)}")
        return video_ids
    except Exception as e:
        print(f"Error fetching videos: {e}")
        raise e


def batch_list(video_id_lst, batch_size):
    for i in range(0, len(video_id_lst), batch_size):
        yield video_id_lst[i : i + batch_size]

@task 
def extract_video_data(video_ids):
    if not video_ids:
        raise ValueError("video_ids list is empty")
        
    extracted_data = []

    try:
        for batch in batch_list(video_ids, 50):
            video_ids_str = ",".join(batch)
            url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,statistics&id={video_ids_str}&key={API_KEY}"

            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                video_data = {
                    "video_id": item['id'],
                    "title": item.get('snippet', {}).get('title'),
                    "publishedAt": item.get('snippet', {}).get('publishedAt'),
                    "duration": item.get('contentDetails', {}).get('duration'),
                    "viewCount": item.get('statistics', {}).get('viewCount'),
                    "likeCount": item.get('statistics', {}).get('likeCount'),
                    "commentCount": item.get('statistics', {}).get('commentCount')
                }
                extracted_data.append(video_data)
        
        print(f"Successfully extracted data for {len(extracted_data)} videos")
        return extracted_data

    except Exception as e:
        print(f"Error extracting data: {e}")
        raise e

@task 
def save_to_json(extracted_data):
    if not extracted_data:
        print("No data to save.")
        return

    output_dir = "/opt/airflow/data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    file_path = f"{output_dir}/YT_data_{date.today()}.json"

    with open(file_path, "w", encoding="utf-8") as json_outfile:
        json.dump(extracted_data, json_outfile, indent=4, ensure_ascii=False)
    
    print(f"Data successfully saved to {file_path}")