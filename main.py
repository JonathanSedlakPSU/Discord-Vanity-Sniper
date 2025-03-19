#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import random
import time
from itertools import cycle
from datetime import datetime
from requests.adapters import HTTPAdapter

try:
    import requests
    from bs4 import BeautifulSoup
    from dotenv import dotenv_values
    from user_agent import generate_user_agent
    config = dotenv_values(".env")
except Exception as e:
    print(e)

# Set console title and clear screen
os.system('title Discord Vanity Sniper')
os.system('cls' if os.name == 'nt' else 'clear')


class Sniper:
    """
    A class to attempt sniping a Discord vanity URL using available proxies.
    
    It scrapes proxy lists, cycles through them, and tries to change the guild vanity URL.
    """

    def __init__(self) -> None:
        self.vanity_url: str = config.get("VANITY_URL")
        self.guild_id: str = config.get("GUILD_ID")
        self.token: str = config.get("TOKEN")

        self.headers = {
            "authorization": self.token,
            "user-agent": generate_user_agent()
        }
        self.payload = {"code": self.vanity_url}

        self.session = requests.Session()
        self.session.mount("", HTTPAdapter(max_retries=1))

        self.proxy_pool = cycle(self.grab_proxies())
        self.proxy = next(self.proxy_pool)

    def grab_proxies(self) -> list[str]:
        """
        Scrape proxies from multiple sources and return a shuffled list with a termination marker.
        
        Returns:
            list[str]: A list of proxy strings, with "end" appended.
        """
        proxies = set()

        # Grab proxies from sslproxies.org
        page = self._make_request("https://sslproxies.org/", method="get", proxies={})
        if page and hasattr(page, "text"):
            soup = BeautifulSoup(page.text, "html.parser")
            table = soup.find("table", attrs={"class": "table table-striped table-bordered"})
            if table:
                for row in table.find_all("tr"):
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        # Construct proxy in ip:port format
                        proxy = f"{cells[0].text.strip()}:{cells[1].text.strip()}"
                        proxies.add(proxy)

        # Grab proxies from proxy-list.download
        text = self._make_request(
            "https://www.proxy-list.download/api/v1/get?type=https",
            method="get",
            proxies={}
        )
        if text and hasattr(text, "text"):
            for proxy in text.text.splitlines():
                if proxy:
                    proxies.add(proxy.strip())

        proxies = list(proxies)
        random.shuffle(proxies)
        proxies.append("end")
        return proxies

    def change_vanity(self) -> None:
        """
        Attempt to change the guild vanity URL.
        
        If successful, the process is terminated.
        """
        url = f"https://discord.com/api/v9/guilds/{self.guild_id}/vanity-url"
        response = self._make_request(url=url, method="patch", proxies={"https": self.proxy})
        try:
            if response and response.status_code == 200:
                print(f"{datetime.now().strftime('[On %Y-%m-%d @ %H:%M:%S]')} VANITY SNIPED: discord.gg/{self.vanity_url} has been sniped successfully!")
                os._exit(1)
            else:
                print(f"{datetime.now().strftime('[On %Y-%m-%d @ %H:%M:%S]')} Could not snipe discord.gg/{self.vanity_url}! "
                      f"Status Code: {response.status_code if response else 'No Response'} | Better luck next time :(")
        except Exception:
            print(f"change_vanity error: {response}")

    def check_vanity(self) -> None:
        """
        Check if the vanity URL is available and attempt to change it if free.
        """
        url = f"https://discord.com/api/v9/invites/{self.vanity_url}?with_counts=true&with_expiration=true"
        response = self._make_request(url=url, method="get", proxies={"https": self.proxy})
        try:
            if response and response.status_code == 404:
                print(f"{datetime.now().strftime('[On %Y-%m-%d @ %H:%M:%S]')} Proxy is free, trying to change: {self.proxy}")
                self.change_vanity()
            elif response and response.status_code == 200:
                print(f"{datetime.now().strftime('[On %Y-%m-%d @ %H:%M:%S]')} Proxy is good: {self.proxy} but URL is still taken, sleeping for 30 seconds")
                time.sleep(30)
                self.check_vanity()
            elif response and response.status_code == 429:
                print(f"{datetime.now().strftime('[On %Y-%m-%d @ %H:%M:%S]')} Proxy has made too many requests: {self.proxy}")
            else:
                code = response.status_code if response else "No Response"
                print(f"{datetime.now().strftime('[On %Y-%m-%d @ %H:%M:%S]')} Status code: {code} - Proxy: {self.proxy} - still taken. Attempting to snipe discord.gg/{self.vanity_url}")
        except Exception:
            print(f"{datetime.now().strftime('[On %Y-%m-%d @ %H:%M:%S]')} check_vanity error: {response}")

    def _make_request(self, url: str, method: str, proxies: dict) -> requests.Response | None:
        """
        Helper method to perform an HTTP request with the given method.

        Args:
            url (str): The target URL.
            method (str): The HTTP method ("get" or "patch").
            proxies (dict): The proxies to use.

        Returns:
            requests.Response | None: The response object or None on error.
        """
        try:
            if method.lower() == "get":
                return self.session.get(
                    url, timeout=5, proxies=proxies,
                    headers={"user-agent": generate_user_agent()}
                )
            elif method.lower() == "patch":
                return self.session.patch(
                    url, timeout=5, proxies=proxies,
                    headers=self.headers, json=self.payload
                )
        except requests.exceptions.Timeout:
            print(f"Timeout - {self.proxy}")
        except requests.exceptions.ProxyError:
            print(f"ProxyError - {self.proxy}")
        except requests.exceptions.SSLError:
            print(f"SSLError - {self.proxy}")
        return None

    def start(self) -> None:
        """
        Main loop to check and snipe the vanity URL using proxies.
        
        Cycles through proxies until the termination marker ("end") is reached,
        then restarts the process with a new instance.
        """
        while self.proxy != "end":
            self.check_vanity()
            self.proxy = next(self.proxy_pool)
        # Restart the process if all proxies are exhausted
        Sniper().start()


if __name__ == "__main__":
    # If requirements are not set via environment variable, run the batch file and exit.
    if not os.getenv('requirements'):
        subprocess.Popen(['start', 'start.bat'], shell=True)
        sys.exit()

    os.system('cls' if os.name == 'nt' else 'clear')
    Sniper().start()
