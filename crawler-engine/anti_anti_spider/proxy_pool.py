"""Dynamic proxy IP pool for crawlers.

Modes: xiaoxiang, tunnel, none.
Xiaoxiang short-lived proxy IPs expire in 2-5 minutes.
Set PROXY_REFRESH_INTERVAL to 60-120s to rotate before they die.
"""
import os
import json
import re
import threading
import time
from typing import Optional

import httpx
from loguru import logger


class ProxyPool:

    def __init__(self):
        self._mode = os.getenv("PROXY_MODE", "none").lower()
        self._lock = threading.Lock()
        self._api_url = os.getenv("PROXY_API_URL", "")
        self._refresh_interval = int(os.getenv("PROXY_REFRESH_INTERVAL", "60"))
        self._tunnel_host = os.getenv("PROXY_TUNNEL_HOST", "")
        self._tunnel_port = os.getenv("PROXY_TUNNEL_PORT", "")
        self._username = os.getenv("PROXY_USERNAME", "")
        self._password = os.getenv("PROXY_PASSWORD", "")
        self._pool = []
        self._last_refresh = 0.0
        self._index = 0
        self._current = None

        if self._mode == "xiaoxiang" and not self._api_url:
            logger.warning("xiaoxiang mode but PROXY_API_URL is empty; falling back to direct")
            self._mode = "none"
        elif self._mode == "tunnel" and not self._tunnel_host:
            logger.warning("tunnel mode but PROXY_TUNNEL_HOST is empty; falling back to direct")
            self._mode = "none"
        elif self._mode == "none":
            logger.warning("DIRECT MODE - your real IP is exposed! For testing only.")

        logger.info(f"ProxyPool | mode={self._mode}")

    @property
    def mode(self):
        return self._mode

    @property
    def pool_size(self):
        return len(self._pool)

    def get(self):
        if self._mode == "none":
            return None
        if self._mode == "tunnel":
            return self._tunnel_proxy()
        if self._mode == "xiaoxiang":
            return self._pool_proxy()
        return None

    def report_failure(self, proxy):
        """Call when proxy returns connection error / 403 / timeout.
        Short-lived IPs expire in 2-5 min and will fail; this rotates them out."""
        if self._mode != "xiaoxiang" or not proxy:
            return
        with self._lock:
            before = len(self._pool)
            ip_key = proxy.get("ip") if isinstance(proxy, dict) else str(proxy)
            self._pool = [p for p in self._pool if p.get("ip") not in ip_key]
            removed = before - len(self._pool)
            if removed:
                logger.warning(f"Removed {removed} dead/likely expired proxy, {len(self._pool)} remaining")
                if not self._pool:
                    logger.info("Proxy pool empty, will force refresh on next get()")
                    self._last_refresh = 0

    def _pool_proxy(self):
        self._ensure_pool()
        with self._lock:
            if not self._pool:
                return None
            self._index = (self._index + 1) % len(self._pool)
            entry = self._pool[self._index]
        url = f"http://{entry['ip']}:{entry['port']}"
        self._current = {"ip": entry["ip"], "port": entry["port"], "url": url}
        return url

    def _ensure_pool(self):
        now = time.time()
        if self._pool and (now - self._last_refresh) < self._refresh_interval:
            return
        self._refresh_pool()

    def _refresh_pool(self):
        try:
            resp = httpx.get(self._api_url, timeout=15)
            text = resp.text.strip()
            if not text:
                logger.warning("Proxy API returned empty response")
                return
            new_pool = []
            found = self._try_json(text, new_pool)
            if not found:
                self._try_text(text, new_pool)
            if not new_pool:
                logger.warning(f"Proxy API returned unparseable response: {text[:80]}")
                return
            with self._lock:
                self._pool = new_pool
                self._last_refresh = time.time()
                self._index = 0
            logger.info(f"Fetched {len(new_pool)} proxies, refresh every {self._refresh_interval}s")
        except Exception as e:
            logger.warning(f"Proxy API request failed: {e}")

    def _try_json(self, text, pool):
        """Try to parse JSON response (Xiaoxiang API format)."""
        try:
            data = json.loads(text)
            items = None
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if data.get("success") or data.get("code") == 200:
                    items = data.get("data", [])
            if items:
                for item in items:
                    if isinstance(item, dict) and "ip" in item:
                        entry = {"ip": item["ip"], "port": item["port"]}
                        during = item.get("during")
                        if during and during > 0:
                            suggested = max(int(during) * 30, 30)
                            if suggested < self._refresh_interval:
                                self._refresh_interval = suggested
                        pool.append(entry)
                return True
        except Exception:
            pass
        return False

    def _try_text(self, text, pool):
        """Try to parse text format (ip:port pairs)."""
        for match in re.finditer(r"(\d+\.\d+\.\d+\.\d+):(\d+)", text):
            port = int(match.group(2))
            if port <= 65535:
                pool.append({"ip": match.group(1), "port": port})
        seen = set()
        deduped = []
        for item in pool:
            if item["ip"] not in seen:
                seen.add(item["ip"])
                deduped.append(item)
        pool.clear()
        pool.extend(deduped)

    def _tunnel_proxy(self):
        if not self._username:
            url = f"http://{self._tunnel_host}:{self._tunnel_port}"
        else:
            url = f"http://{self._username}:{self._password}@{self._tunnel_host}:{self._tunnel_port}"
        return url

    def __repr__(self):
        return f"ProxyPool(mode={self._mode}, pool_size={len(self._pool)})"
