import random
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .doh import set_doh_enabled


class WaifuDownloaderAPI:
	def __init__(self, use_doh=False):
		self.endpoint = "https://api.waifu.im/images"
		self.session = requests.Session()
		retry = Retry(
			total=1,
			connect=1,
			read=1,
			status=1,
			backoff_factor=0.5,
			status_forcelist=(429, 500, 502, 503, 504),
			allowed_methods=frozenset(("GET",)),
			respect_retry_after_header=True,
		)
		self.session.mount("https://", HTTPAdapter(max_retries=retry))
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

	def get_random_image(self, nsfw=False, search_term="", provider="Auto"):
		"""Fetch an image, falling back across providers in Auto mode."""
		if provider != "Auto":
			url = self.get_neko(nsfw, search_term, provider)
			return self.info, self.get_image(url)

		errors = []
		for name in ("Waifu.im", "Danbooru", "yande.re"):
			try:
				url = self.get_neko(nsfw, search_term, name)
				content = self.get_image(url)
				return self.info, content
			except (requests.RequestException, ValueError) as error:
				errors.append(f"{name}: {error}")
		raise RuntimeError("All providers failed: " + " | ".join(errors))

	def _get_waifu_im(self, nsfw, search_term):
		params = {"IsNsfw": str(nsfw), "PageSize": 1}
		included_tags = ["waifu"]
		if search_term:
			included_tags.append(search_term.casefold().replace(" ", "-"))
		params["IncludedTags"] = included_tags
		response = self.session.get(self.endpoint, params=params, timeout=(5, 15))
		response.raise_for_status()
		data = response.json()
		images = data.get("items") or []
		if not images or not images[0].get("url"):
			self._no_results(search_term)
		self.info = data
		return images[0]["url"]

	def _get_danbooru(self, nsfw, search_term):
		tags = self._booru_search_tags(search_term, prefix_match=True)
		posts = self._get_booru_posts(
			"https://danbooru.donmai.us/posts.json", tags, nsfw
		)
		self._set_booru_result(posts, search_term, nsfw)
		return self.info["items"][0]["url"]

	def _get_yandere(self, nsfw, search_term):
		tags = self._booru_search_tags(search_term, prefix_match=True)
		posts = self._get_booru_posts(
			"https://yande.re/post.json", tags, nsfw, yandere=True
		)
		self._set_booru_result(posts, search_term, nsfw)
		return self.info["items"][0]["url"]

	def _get_booru_posts(self, endpoint, tags, nsfw, yandere=False):
		# Never use -rating:s for NSFW: it also matches general/unrated posts.
		# Query questionable and explicit separately, then combine the matches.
		ratings = ("q", "e") if nsfw else ("s",)
		posts = []
		for rating in ratings:
			# Keep the remote query small: Danbooru rejects long anonymous queries.
			# Gender filtering is applied locally to the returned post metadata.
			query_tags = [*tags, f"rating:{rating}"]
			if yandere:
				query_tags.append("order:random")
				params = {"api_version": 2, "tags": " ".join(query_tags), "limit": 100}
			else:
				params = {"tags": " ".join(query_tags), "limit": 100, "random": 1}
			response = self.session.get(endpoint, params=params, timeout=(5, 20))
			response.raise_for_status()
			result = response.json()
			if isinstance(result, dict):
				result = result.get("posts", [])
			posts.extend(post for post in result if post.get("rating") == rating)
		return posts

	def _set_booru_result(self, posts, search_term, nsfw):
		if not isinstance(posts, list):
			posts = posts.get("posts", [])
		allowed_ratings = ("q", "e") if nsfw else ("s",)
		girl_tags = {"1girl", "2girls", "3girls", "4girls", "5girls", "6+girls", "female_focus"}
		boy_tags = {"1boy", "2boys", "3boys", "4boys", "5boys", "6+boys", "male_focus", "male_only"}
		posts = [
			post for post in posts
			if post.get("rating") in allowed_ratings
			and self._post_tags(post).intersection(girl_tags)
			and not self._post_tags(post).intersection(boy_tags)
			and self._post_url(post)
		]
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
	def _post_tags(post):
		values = [
			post.get("tag_string"),
			post.get("tag_string_general"),
			post.get("tag_string_character"),
			post.get("tag_string_copyright"),
			post.get("tag_string_artist"),
			post.get("tags"),
		]
		tags = set()
		for value in values:
			if isinstance(value, str):
				tags.update(value.casefold().split())
			elif isinstance(value, dict):
				tags.update(str(tag).casefold() for tag in value.values())
			elif isinstance(value, list):
				for tag in value:
					if isinstance(tag, dict):
						name = tag.get("name")
						if name:
							tags.add(str(name).casefold())
					elif isinstance(tag, str):
						tags.add(tag.casefold())
		return tags

	@staticmethod
	def _booru_search_tags(search_term, prefix_match=False):
		query = search_term.strip()
		if " " in query and "_" not in query:
			query = query.replace(" ", "_")
		tags = query.split()
		if prefix_match and len(tags) == 1:
			tag = tags[0]
			if tag and not any(char in tag for char in "*~()") and ":" not in tag and not tag.startswith("-"):
				tags[0] = f"{tag}*"
		return tags

	@staticmethod
	def _no_results(search_term):
		if search_term:
				raise ValueError(f"No images matched the tag '{search_term}'.")
		raise ValueError("The provider returned no images.")

	def get_image(self, url):
		response = self.session.get(url, timeout=(5, 25))
		response.raise_for_status()
		return response.content
