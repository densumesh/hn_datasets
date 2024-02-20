import csv
import requests
import csv
from tqdm import tqdm
import redis
import os
from trieve_client import AuthenticatedClient
from trieve_client.models import CreateChunkData, ReturnCreatedChunk, ErrorResponseBody
from trieve_client.api.chunk import create_chunk
from datetime import datetime

# Connect to Redis
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    password="thisredispasswordisverysecureandcomplex",
)
header = [
    "by",
    "descendants",
    "id",
    "kids",
    "score",
    "time",
    "title",
    "text",
    "type",
    "url",
]


trieve_client = AuthenticatedClient(
    base_url="https://api.trieve.ai",
    prefix="",
    token="tr-6b3fb3MXYs799XuAryTfGzJZmGffN6S3",
).with_headers(
    {
        "TR-Organization": "2ccba845-f621-4c86-abe0-bdfa6ff8e637",
    }
)


def intialize_files():
    if not os.path.exists("hacker_news_stories.csv"):
        print("Creating hacker_news_stories.csv")
        with open("hacker_news_stories.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(header)
    if not os.path.exists("hacker_news_comments.csv"):
        print("Creating hacker_news_comments.csv")
        with open("hacker_news_comments.csv", "w") as file:
            writer = csv.writer(file)
            writer.writerow(header)


def ingest_hn():
    intialize_files()
    final = int(
        requests.get("https://hacker-news.firebaseio.com/v0/maxitem.json").json()
    )
    for i in tqdm(range(final, final - 10000, -1)):
        # Check if item ID is already present
        if redis_client.exists("hn:" + str(i)):
            continue

        # Add item ID to Redis
        redis_client.set("hn:" + str(i), 1)
        item = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{i}.json"
        ).json()

        if (
            item
            and "type" in item
            and ("title" in item or "text" in item)
            and "deleted" not in item
            and "dead" not in item
            and item["type"] == "story"
        ):
            row = {
                "by": item.get("by"),
                "descendants": item.get("descendants"),
                "id": item.get("id"),
                "kids": item.get("kids"),
                "score": item.get("score"),
                "time": item.get("time"),
                "title": item.get("title"),
                "text": (
                    item.get("text").strip().replace("\n", " ").replace("\r", " ")
                    if item.get("text")
                    else None
                ),
                "type": item.get("type"),
                "url": item.get("url"),
            }

            data = CreateChunkData(
                chunk_html=row["title"],
                link=row["url"],
                metadata={
                    "by": row.get("by"),
                    "descendants": row.get("descendants"),
                    "id": row.get("id"),
                    "kids": row.get("kids"),
                    "score": row.get("score"),
                    "time": row.get("time"),
                    "title": row.get("title"),
                    "text": row.get("text"),
                    "type": row.get("type"),
                },
                tracking_id=str(row.get("id")),
                time_stamp=datetime.fromtimestamp(row.get("time")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
            chunk_response = create_chunk.sync(
                tr_dataset="23aba24b-98d4-4ca6-af99-4305446a12fe",
                client=trieve_client,
                body=data,
            )
            if type(chunk_response) == ErrorResponseBody:
                print(f"Failed {chunk_response.message}")
                exit(1)
        elif (
            item
            and "type" in item
            and "deleted" not in item
            and "dead" not in item
            and item["type"] == "comment"
        ):
            row = {
                "by": item.get("by"),
                "descendants": item.get("descendants"),
                "id": item.get("id"),
                "kids": item.get("kids"),
                "score": item.get("score"),
                "time": item.get("time"),
                "title": item.get("title"),
                "text": (
                    item.get("text").strip().replace("\n", " ").replace("\r", " ")
                    if item.get("text")
                    else None
                ),
                "type": item.get("type"),
                "url": item.get("url"),
            }

            data = CreateChunkData(
                chunk_html=row["text"],
                link=row["url"],
                metadata={
                    "by": row.get("by"),
                    "descendants": row.get("descendants"),
                    "id": row.get("id"),
                    "kids": row.get("kids"),
                    "score": row.get("score"),
                    "time": row.get("time"),
                    "title": row.get("title"),
                    "text": row.get("text"),
                    "type": row.get("type"),
                },
                tracking_id=str(row.get("id")),
                time_stamp=datetime.fromtimestamp(row.get("time")).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            )
            chunk_response = create_chunk.sync(
                tr_dataset="8cd1414f-8e3d-41d3-a0fc-1d9dd66f21a5",
                client=trieve_client,
                body=data,
            )
            if type(chunk_response) == ErrorResponseBody:
                print(f"Failed {chunk_response.message}")
                exit(1)


ingest_hn()
