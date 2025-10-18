import time
import threading

# Constants (equivalent to C macros)
MAX_CACHE_SIZE = 200 * (1 << 20)        # 200 MB
MAX_ELEMENT_SIZE = 10 * (1 << 20)       # 10 MB


class CacheElement:
    def __init__(self, data: bytes, url: str):
        self.data = data
        self.len = len(data)
        self.url = url
        self.lru_time_track = time.time()


class Cache:
    def __init__(self):
        self.cache_size = 0
        self.elements = {}  # Use dict for O(1) access by URL
        self.lock = threading.Lock()

    def cache_find(self, url: str):
        if not url:
            return None

        with self.lock:
            element = self.elements.get(url)
            if element:
                element.lru_time_track = time.time()
                print(f"[CACHE] Found URL: {url}, updated LRU time")
                return element

            print(f"[CACHE] URL not found in cache: {url}")
            return None

    def cache_remove(self):
        with self.lock:
            if not self.elements:
                return

            # Find oldest element by timestamp
            lru_url = min(self.elements, key=lambda u: self.elements[u].lru_time_track)
            lru = self.elements[lru_url]

            element_size = lru.len + len(lru.url) + 1
            self.cache_size -= element_size

            print(f"[CACHE] Removing URL: {lru.url}, freed {element_size} bytes")
            del self.elements[lru_url]

    def cache_add(self, data: bytes, url: str) -> bool:
        if not data or not url:
            return False

        size = len(data)
        element_size = size + len(url) + 1

        if element_size > MAX_ELEMENT_SIZE:
            print(f"[CACHE] Element too large, skipping: {url}")
            return False

        with self.lock:
            # If exists, update
            if url in self.elements:
                existing = self.elements[url]
                existing.data = data
                existing.len = size
                existing.lru_time_track = time.time()
                print(f"[CACHE] Updated existing URL: {url}")
                return True

            # Ensure enough space
            while self.cache_size + element_size > MAX_CACHE_SIZE and self.elements:
                self.cache_remove()

            # Add new
            element = CacheElement(data, url)
            self.elements[url] = element
            self.cache_size += element_size

            print(f"[CACHE] Added URL: {url}, size: {size} bytes, total: {self.cache_size}")
            return True

    def cache_print(self):
        with self.lock:
            print("-----CACHE CONTENTS-----")
            print(f"Total cache size: {self.cache_size} bytes")
            for i, (url, elem) in enumerate(self.elements.items(), 1):
                print(f"{i}. URL: {url}, Size: {elem.len}, LRU: {elem.lru_time_track}")
            print("------------------------")

    def cache_get_size(self):
        with self.lock:
            return self.cache_size

    def cache_clear(self):
        with self.lock:
            self.elements.clear()
            self.cache_size = 0
            print("[CACHE] Cache cleared")

    def cache_exists(self, url: str) -> bool:
        with self.lock:
            return url in self.elements

    def cache_update_lru(self, url: str):
        with self.lock:
            if url in self.elements:
                self.elements[url].lru_time_track = time.time()
                print(f"[CACHE] Updated LRU for {url}")


# ✅ Singleton instance (like global variables in C)
cache = Cache()
