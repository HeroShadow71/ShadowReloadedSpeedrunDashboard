"""
Small Speedrun.com API client utilities.

Provides the `ApiClient` class - a small wrapper that centralizes URL
construction and handles basic pagination logic used by the application.
"""
from dashboard_core.api_utils import fetch_api_cached
from constants import API_TIMEOUT, API_PAGE_SIZE


class ApiClient:
    """
    Client for the Speedrun.com API used by the app.

    Wraps endpoint access with convenience methods and optional caching.
    
    :param base_url: base API URL
    :param timeout: request timeout in seconds
    :param page_size: default page size for paginated endpoints
    """

    def __init__(
        self,
        base_url="https://www.speedrun.com/api/v1",
        timeout=API_TIMEOUT,
        page_size=API_PAGE_SIZE
    ):
        self.base = base_url.rstrip("/")
        self.timeout = timeout
        self.page_size = page_size

    def get_runs(self, game_id, offset=0, max=None, cache_file=None):
        """
        Fetch a page of runs for a given game.

        :param game_id: Speedrun.com game ID
        :param offset: pagination offset
        :param max: page size override
        :param cache_file: optional cache file Path passed to fetch_api_cached
        :return: list of run dictionaries
        """
        m = max or self.page_size
        url = f"{self.base}/runs?game={game_id}&max={m}&offset={offset}"
        return fetch_api_cached(url, cache_file=cache_file, timeout=self.timeout)

    def get_categories(self, game_id, cache_file=None):
        """
        Return category data for a game from the API (or cache).

        :param game_id: Speedrun.com game id
        :param cache_file: optional cache file Path
        :return: API response data
        """
        url = f"{self.base}/games/{game_id}/categories"
        return fetch_api_cached(url, cache_file=cache_file, timeout=self.timeout)

    def get_levels(self, game_id, cache_file=None):
        """
        Return level data for a game from the API (or cache).

        :param game_id: Speedrun.com game id
        :param cache_file: optional cache file Path
        :return: API response data
        """
        url = f"{self.base}/games/{game_id}/levels"
        return fetch_api_cached(url, cache_file=cache_file, timeout=self.timeout)

    def get_user(self, user_id, cache_file=None):
        """
        Return user data for a given user id.

        :param user_id: Speedrun.com user id
        :param cache_file: optional cache file Path
        :return: API response data
        """
        url = f"{self.base}/users/{user_id}"
        return fetch_api_cached(url, cache_file=cache_file, timeout=self.timeout)

    def get_all_runs(self, game_id, cache_file=None, max_pages=None, page_size=None):
        """
        Fetch all runs for a game by paging through the API.

        Combines results from multiple pages into a single list.

        :param game_id: Speedrun.com game ID
        :param cache_file: optional Path to cache file for fetch_api_cached
        :param max_pages: maximum number of pages to fetch (None = all)
        :param page_size: number of items per page (overrides client default)
        :return: list of run dictionaries
        """
        offset = 0
        all_runs = []
        pages_fetched = 0
        
        while True:
            # Allow caller to override per-page size via 'page_size'.
            # If omitted, `get_runs` uses the client's configured `page_size`
            page = self.get_runs(game_id, offset=offset, max=page_size, cache_file=cache_file)
            if not page:
                break
            
            all_runs.extend(page)
            pages_fetched += 1
            
            # Stop early if max_pages was specified.
            if max_pages is not None and pages_fetched >= int(max_pages):
                break
            
            # Advance offset for the next request using the actual page size.
            used_page = int(page_size) if page_size is not None else self.page_size
            offset += used_page

        return all_runs
