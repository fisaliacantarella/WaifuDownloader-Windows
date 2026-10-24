import random
from urllib.parse import urlparse

import requests

from .doh import set_doh_enabled


class WaifuDownloaderAPI:
	def __init__(self, use_doh=False):
		self.endpoint = "https://api.waifu.im/images"
		self.session = requests.Session()
		self.session.headers.update({
			"User-Agent": "Waifu Downloader for Windows/0.3 (desktop image viewer)",
			"Accept-Version": "v7",
		})
		self.use_doh = use_doh
		self.info = None

	def get_neko(self, nsfw=False, search_term="", provider="Waifu.im"):
		set_doh_enabled(self.use_doh)
		providers = {
			"Waifu.im": self._get_waifu_im,
			"Danbooru": self._get_danbooru,
			"yande.re": self._get_yandere,
		}
		if provider == "Auto":
			errors = []
			for name, search in providers.items():
				try:
					return search(nsfw, search_term)
				except (requests.RequestException, ValueError) as error:
					errors.append(f"{name}: {error}")
			raise RuntimeError("All providers failed: " + " | ".join(errors))
		if provider == "Danbooru":
			return self._get_danbooru(nsfw, search_term)
		if provider == "yande.re":
			return self._get_yandere(nsfw, search_term)
		if provider == "Waifu.im":
			return self._get_waifu_im(nsfw, search_term)
		raise ValueError(f"Unknown provider: {provider}")

	def _get_waifu_im(self, nsfw, search_term):
		params = {"IsNsfw": str(nsfw), "PageSize": 1}
		if search_term:
			params["IncludedTags"] = search_term.casefold().replace(" ", "-")
		response = self.session.get(self.endpoint, params=params, timeout=15)
		response.raise_for_status()
		data = response.json()
		images = data.get("items") or []
		if not images or not images[0].get("url"):
			self._no_results(search_term)
		self.info = data
		return images[0]["url"]

	def _get_danbooru(self, nsfw, search_term):
		tags = self._booru_search_tags(search_term)
		tags.append("-rating:s" if nsfw else "rating:s")
		response = self.session.get(
			"https://danbooru.donmai.us/posts.json",
			params={"tags": " ".join(tags), "limit": 20, "random": 1},
			timeout=20,
		)
		response.raise_for_status()
		posts = response.json()
		self._set_booru_result(posts, search_term)
		return self.info["items"][0]["url"]

	def _get_yandere(self, nsfw, search_term):
		tags = self._booru_search_tags(search_term)
		tags.extend(["-rating:s" if nsfw else "rating:s", "order:random"])
		response = self.session.get(
			"https://yande.re/post.json",
			params={"api_version": 2, "tags": " ".join(tags), "limit": 20},
			timeout=20,
		)
		response.raise_for_status()
		posts = response.json()
		self._set_booru_result(posts, search_term)
		return self.info["items"][0]["url"]

	def _set_booru_result(self, posts, search_term):
		if not isinstance(posts, list):
			posts = posts.get("posts", [])
		posts = [post for post in posts if self._post_url(post)]
		if not posts:
			self._no_results(search_term)
		post = random.choice(posts)
		url = self._post_url(post)
		extension = post.get("file_ext") or urlparse(url).path.rsplit(".", 1)[-1]
		artists = post.get("tag_string_artist", "").split()
		self.info = {
			"items": [{
				"id": post.get("id", "image"),
				"url": url,
				"extension": f".{extension.lstrip('.')}",
				"source": post.get("source", ""),
				"artists": [{"name": artist} for artist in artists],
				"tags": post.get("tags", ""),
			}],
		}

	@staticmethod
	def _post_url(post):
		return post.get("file_url") or post.get("large_file_url") or post.get("sample_url") or post.get("jpeg_url")

	@staticmethod
	def _booru_search_tags(search_term):
		query = search_term.strip()
		if " " in query and "_" not in query:
			query = query.replace(" ", "_")
		return query.split()

	@staticmethod
	def _no_results(search_term):
		if search_term:
				raise ValueError(f"No images matched the tag '{search_term}'.")
		raise ValueError("The provider returned no images.")

	def get_image(self, url):
		response = self.session.get(url, timeout=30)
		response.raise_for_status()
		return response.content
