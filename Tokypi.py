import os
import asyncio
import aiohttp
import requests
from typing import Union, Optional, List, Dict
from datetime import datetime
from parsel import Selector
import json
import re


class Connection:
	BASE: str = "https://tokybook.com/"
	SEARCH: str = f"{BASE}?s="
	status_code: Optional[int] = None

	def check_status(self) -> str:
		response = requests.get(self.BASE)
		response.raise_for_status()
		self.status_code = response.status_code
		return "Success"


class Search(Connection):
	def __init__(self, query: Optional[str] = None) -> None:
		super().__init__()
		self.query: Optional[str] = query

	def results(self) -> Union[str, List[Dict]]:
		status = self.check_status()
		if status != "Success":
			return f"Error: Status Code {status}"
		if not self.query:
			return "No query provided."

		response = requests.get(self.SEARCH + self.query)
		return self._extract_results(response)

	def _extract_results(self, response: requests.Response) -> List[Dict]:
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

	async def download_all_books(self) -> None:
		results = self.results()
		if results:
			for result in results:
				book_url = result["link"]
				book = Book(book_url)
				book_title = result["book_title"]
				book_folder_path = os.path.join(".", book_title)
				await book.download_episodes(book_folder_path)
		else:
			print("No search results found.")


class Book(Search):
	EXCLUDE = "https://file.tokybook.com/upload/welcome-you-to-tokybook.mp3"

	def __init__(self, book_url: str) -> None:
		super().__init__()
		self.book_url = book_url

	async def download_episode(self, session: aiohttp.ClientSession, episode_title: str, episode_url: str, episode_file_path: str) -> None:
		print(f"Downloading {episode_title}...")
		async with session.get(episode_url) as response:
			with open(episode_file_path, "wb") as f:
				f.write(await response.read())
		print(f"{episode_title} downloaded successfully.")

	async def download_episodes(self, download_path: str) -> None:
		episodes = self.episodes()
		if not os.path.exists(download_path):
			os.makedirs(download_path)
		async with aiohttp.ClientSession() as session:
			tasks = []
			for episode in episodes:
				episode_title = episode["name"]
				episode_url = episode["url"]
				episode_file_path = os.path.join(download_path, f"{episode_title}.mp3")
				if not os.path.exists(episode_file_path):
					tasks.append(self.download_episode(session, episode_title, episode_url, episode_file_path))
			await asyncio.gather(*tasks)

	def episodes(self) -> List[Dict]:
		response = requests.get(self.book_url)
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
