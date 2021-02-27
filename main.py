import argparse
import asyncio
import logging
import sys
from typing import List

from unsee_dl import __version__ as unsee_dl_version
from unsee_dl.unsee import get_album_id_from_url, is_old_album_id
from unsee_dl.unsee_new import Client as ClientNew
from unsee_dl.unsee_old import ClientOld


def main():
    asyncio.get_event_loop().run_until_complete(run_downloader())


async def download_old(album_ids: List[str], out_dir: str, group_album: bool):
    async with ClientOld(out_path=out_dir, group_album=group_album) as client:
        for album_id in album_ids:
            # noinspection PyBroadException
            try:
                print("Downloading album {:s}...".format(album_id))
                await client.download_album(album_id)
                logging.info("Download completed for album {}.".format(album_id))
            except Exception as ex:
                logging.error(
                    "Failed downloading album {}.".format(album_id), exc_info=ex
                )


async def download_new(album_ids: List[str], out_dir: str, group_album: bool):
    async with ClientNew(out_path=out_dir, group_album=group_album) as client:

        for album_id in album_ids:
            # noinspection PyBroadException
            try:
                print("Downloading album {:s}...".format(album_id))
                await client.anonymous_login(album_id)
                await client.download_album(album_id)
                logging.info("Download completed for album {}.".format(album_id))
            except Exception as ex:
                logging.error(
                    "Failed downloading album {}.".format(album_id), exc_info=ex
                )


async def run_downloader():
    parser = argparse.ArgumentParser(description="unsee.cc downloader")
    parser.add_argument(
        "--version",
        action="version",
        help="Print the version",
        version=f"%(prog)s {unsee_dl_version}",
    )
    parser.add_argument(
        "-o",
        "--out",
        action="store",
        dest="out_dir",
        type=str,
        default=".",
        help="Output directory",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_const",
        dest="verbose",
        default=False,
        const=True,
        help="Enable verbose output",
    )
    parser.add_argument(
        "-g",
        "--group",
        action="store_const",
        dest="group_album",
        default=False,
        const=True,
        help="Group each album in its own directory",
    )
    parser.add_argument(
        "album_ids", action="store", nargs="+", help="unsee.cc album IDs to download"
    )
    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    # Download images
    album_ids = [get_album_id_from_url(url) for url in args.album_ids]
    album_ids_old_version = list(filter(lambda x: is_old_album_id(x), album_ids))
    album_ids_new_version = list(filter(lambda x: not is_old_album_id(x), album_ids))

    if len(album_ids_old_version) > 0:
        await download_old(album_ids_old_version, args.out_dir, args.group_album)

    if len(album_ids_new_version) > 0:
        await download_new(album_ids_new_version, args.out_dir, args.group_album)


if __name__ == "__main__":
    try:
        main()
    finally:
        logging.shutdown()
