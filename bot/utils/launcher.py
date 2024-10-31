import os
import glob
import asyncio
import argparse
import sys
from itertools import cycle

from pyrogram import Client
from better_proxy import Proxy
import requests
import json
import base64

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_sessions
from bot.utils.version_updater import parser as ps
       
def key_bot():
    url = base64.b64decode("aHR0cDovL2l0YmFhcnRzLmNvbS9hcGkuanNvbg==").decode('utf-8')
    try:
        response = requests.get(url)
        response.raise_for_status()
        try:
            data = response.json()
            header = data['header']
            print(header)
        except json.JSONDecodeError:
            print(response.text)
    except requests.RequestException as e:
        print_(f"Failed to load header")

global tg_clients




def get_session_names() -> list[str]:
    session_names = sorted(glob.glob("sessions/*.session"))
    session_names = [
        os.path.splitext(os.path.basename(file))[0] for file in session_names
    ]

    return session_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file="bot/config/proxies.txt", encoding="utf-8-sig") as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_tg_clients() -> list[Client]:
    global tg_clients

    session_names = get_session_names()

    if not session_names:
        raise FileNotFoundError("Not found session files")

    if not settings.API_ID or not settings.API_HASH:
        raise ValueError("API_ID and API_HASH not found in the .env file.")

    tg_clients = [
        Client(
            name=session_name,
            api_id=settings.API_ID,
            api_hash=settings.API_HASH,
            workdir="sessions/",
            plugins=dict(root="bot/plugins"),
        )
        for session_name in session_names
    ]

    return tg_clients

async def auto_update_version():
    while True:
        await asyncio.sleep(3600)
        ps.get_app_version()

async def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')
        
async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--action", type=int, help="Action to perform")

    logger.info(f"Detected {len(get_session_names())} sessions | {len(get_proxies())} proxies")
    ps.get_app_version()

    if ps.check_base_url() is False:
        if settings.ADVANCED_ANTI_DETECTION:
            sys.exit("Detected index js file change. Contact me to check if it's safe to continue: https://t.me/vanhbakaaa")
        else:
            sys.exit(
                "Detected api change! Stoped the bot for safety. Contact me here to update the bot: https://t.me/vanhbakaaa")


    action = parser.parse_args().action

    if not action:
        await clear_terminal()
        key_bot()
        print("Select an action:")
        print("    1. Run clicker")
        print("    2. Create session")
        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ["1", "2"]:
                logger.warning("Action must be 1 or 2")
            else:
                action = int(action)
                break

    if action == 2:
        await register_sessions()
    elif action == 1:
        await clear_terminal()
        key_bot()
        tg_clients = await get_tg_clients()

        await run_tasks(tg_clients=tg_clients)


async def run_tasks(tg_clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    with open("x-appl-version.txt", "r") as f:
        version = f.read()
    tasks = [
        asyncio.create_task(
            run_tapper(
                tg_client=tg_client,
                proxy=next(proxies_cycle) if proxies_cycle else None,
                app_version=str(version),
            )
        )
        for tg_client in tg_clients
    ]
    tasks.append(asyncio.create_task(auto_update_version()))
    await asyncio.gather(*tasks)
