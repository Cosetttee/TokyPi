import os
import asyncio
import aiohttp
import requests
from typing import List, Dict
from datetime import datetime
from parsel import Selector
import json
import re
import aiofiles
from termcolor import colored

class TokipiDownloader:
    def __init__(self):
        self.BASE_URL: str = "https://tokybook.com/"
        self.SEARCH_URL: str = f"{self.BASE_URL}?s="
        self.EXCLUDE: str = "https://file.tokybook.com/upload/welcome-you-to-tokybook.mp3"

    async def download_episode(self, episode_title: str, episode_url: str, episode_file_path: str) -> None:
        print(f"Downloading {episode_title}...")
        async with aiohttp.ClientSession() as session:
            async with session.get(episode_url) as response:
                async with aiofiles.open(episode_file_path, "wb") as f:
                    await f.write(await response.read())
        print(f"{episode_title} downloaded successfully.")

    async def download_episodes(self, episodes: List[Dict], book_title: str, download_path: str) -> None:
        tasks = []
        for episode in episodes:
            episode_title = episode["name"]
            episode_url = episode["url"]
            episode_file_path = os.path.join(download_path, f"{episode_title}.mp3")
            try:
                os.makedirs(download_path, exist_ok=True)  
                if not os.path.exists(episode_file_path):
                    tasks.append(self.download_episode(episode_title, episode_url, episode_file_path))
            except Exception as e:
                print(f"Error occurred while downloading {episode_title}: {e}")
        await asyncio.gather(*tasks)

    def search(self, query: str) -> List[Dict]:
        response = requests.get(self.SEARCH_URL + query)
        response.raise_for_status()
        return self._extract_search_results(response)

    def _extract_search_results(self, response: requests.Response) -> List[Dict]:
        selector = Selector(text=response.text)
        results: List[Dict] = []
        for article_sel in selector.xpath("//main/article[contains(@class, 'audiobook')]"):
            data: Dict = {}

            post_image_div = article_sel.xpath('.//div[@class="post-image"]').get()
            data["post_image_url"] = Selector(text=post_image_div).xpath(".//img/@src").get()
            data["link"] = Selector(text=post_image_div).xpath(".//a/@href").get()
            data["book_title"] = article_sel.xpath(".//h2/a/text()").get()
            date_published_str = article_sel.xpath(".//time/@datetime").get()
            data["date_published"] = datetime.strptime(date_published_str, "%Y-%m-%dT%H:%M:%S%z").strftime("%B %d, %Y")
            summary = article_sel.xpath('.//div[@class="entry-summary"]/p/text()').get()

            data["summary"] = summary.replace("Tokybook", "").replace("tokybook", "")
            results.append(data)

        return results

    def extract_episodes(self, response: requests.Response) -> List[Dict]:
        chapters = []
        for script in Selector(text=response.text).xpath("//script/text()").extract():
            match = re.search(r"tracks\s*=\s*(\[[^\]]+\])\s*", script)
            if match:
                string = match.group(1).replace("None", "null")
                string = re.sub(r",\s*}", "}", string)
                chapters.extend(json.loads(string))
        tracks = [
            {"name": track["name"], "index": track["track"] - 1, "duration": round(float(track["duration"]) / 60, 1), "url": "https://files02.tokybook.com/audio/" + track["chapter_link_dropbox"]}
            for track in chapters
            if track["chapter_link_dropbox"] != self.EXCLUDE
        ]
        return tracks

async def main():
    downloader = TokipiDownloader()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\nWelcome to Tokipi Audiobook Downloader!")
        search_query = input("Enter the search query for audiobooks (type 'exit' to quit): ")
        if search_query.lower() == 'exit':
            break

        search_results = downloader.search(search_query)
        if search_results:
            print("\nSearch Results:")
            for idx, result in enumerate(search_results, start=1):
                print(f"{colored(idx, 'cyan')}. {colored(result['book_title'], 'yellow')} - {colored(result['date_published'], 'green')}")

            choice = input("\nEnter the number of the book you want to explore or type 'all' to download all books: ")
            if choice.lower() == 'all':
                for result in search_results:
                    book_title = result["book_title"]
                    book_link = result["link"]
                    response = requests.get(book_link)
                    response.raise_for_status()
                    episodes = downloader.extract_episodes(response)
                    download_path = os.path.join(".", book_title)

                    folder_input = input(f"Enter directory path for '{book_title}' downloads (leave blank for current directory): ")
                    download_path = folder_input.strip() or download_path

                    await downloader.download_episodes(episodes, book_title, download_path)
                    print(f"\nAll episodes of '{book_title}' downloaded successfully!")
            elif choice.isdigit() and 1 <= int(choice) <= len(search_results):
                selected_book = search_results[int(choice) - 1]
                book_title = selected_book["book_title"]
                book_link = selected_book["link"]
                response = requests.get(book_link)
                response.raise_for_status()
                episodes = downloader.extract_episodes(response)
                print("\nEpisodes:")
                for idx, episode in enumerate(episodes, start=1):
                    print(f"{colored(idx, 'cyan')}. {colored(episode['name'], 'yellow')} - {colored(episode['duration'], 'green')} minutes")

                download_choice = input("\nDo you want to download all episodes? (yes/no): ")
                if download_choice.lower() == 'yes':
                    folder_input = input(f"Enter directory path for '{book_title}' downloads (leave blank for current directory): ")
                    download_path = os.path.join(".", book_title)

                    await downloader.download_episodes(episodes, book_title, download_path)
                    print(f"\nAll episodes of '{book_title}' downloaded successfully!")
                elif download_choice.lower() == 'no':
                    episode_choice = input("Enter the numbers of the episodes you want to download (comma-separated): ")
                    episode_indices = [int(idx) for idx in episode_choice.split(",")]
                    selected_episodes = [episode for idx, episode in enumerate(episodes, start=1) if idx in episode_indices]

                    folder_input = input(f"Enter directory path for '{book_title}' downloads (leave blank for current directory): ")
                    download_path = os.path.join(".", book_title)

                    await downloader.download_episodes(selected_episodes, book_title, download_path)
                    print(f"\nSelected episodes of '{book_title}' downloaded successfully!")
            else:
                print("Invalid choice. Please enter a valid number or 'all'.")
        else:
            print("No search results found.")

if __name__ == "__main__":
    asyncio.run(main())
