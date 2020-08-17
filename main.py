import argparse
import asyncio
import logging
import sys
from typing import List

from unsee_cc import __version__ as unsee_dl_version


def main():
    asyncio.get_event_loop().run_until_complete(run_downloader())


async def download_unsee_cc(album_ids: List[str], out_dir: str, group_album: bool):
    from unsee_cc.unsee import get_album_id_from_url, is_beta_album_id

    album_ids = [get_album_id_from_url(url) for url in album_ids]
    album_ids_old_version = list(filter(lambda x: not is_beta_album_id(x), album_ids))
    album_ids_beta_version = list(filter(lambda x: is_beta_album_id(x), album_ids))

    if len(album_ids_old_version) > 0:
        await download_unsee_cc_old(album_ids_old_version, out_dir, group_album)

    if len(album_ids_beta_version) > 0:
        await download_unsee_cc_beta(album_ids_beta_version, out_dir, group_album)


async def download_unsee_cc_old(album_ids: List[str], out_dir: str, group_album: bool):
    from unsee_cc.unsee_dl import Client

    async with Client(out_path=out_dir, group_album=group_album) as client:
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


async def download_unsee_cc_beta(album_ids: List[str], out_dir: str, group_album: bool):
    from unsee_cc.unsee_beta import Client as ClientBeta

    async with ClientBeta(out_path=out_dir, group_album=group_album) as client:
        await client.anonymous_login()

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


async def download_unsee_co(album_ids: List[str], out_dir: str, group_album: bool):
    from unsee_co.unsee_co import UnseeCo, get_album_id_from_url

    album_ids = [get_album_id_from_url(url) for url in album_ids]

    async with UnseeCo(out_path=out_dir, group_album=group_album) as client:
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
        "-p",
        "--provider",
        action="store",
        dest="provider",
        type=str,
        default="unseecc",
        help="Image service provider",
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
    if args.provider == "unseecc":
        await download_unsee_cc(args.album_ids, args.out_dir, args.group_album)
    elif args.provider == "unseeco":
        await download_unsee_co(args.album_ids, args.out_dir, args.group_album)

    logging.shutdown()


if __name__ == "__main__":
    main()
