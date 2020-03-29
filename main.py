import argparse
import asyncio
import logging
import sys

from unsee_dl import __version__ as unsee_dl_version
from unsee_dl.unsee import get_album_id_from_url, is_beta_album_id
from unsee_dl.unsee_beta import Client as ClientBeta
from unsee_dl.unsee_dl import Client


def main():
    asyncio.get_event_loop().run_until_complete(run_downloader())


async def run_downloader():
    parser = argparse.ArgumentParser(description="unsee.cc downloader")
    parser.add_argument('--version', action='version', help="Print the version", version=f'%(prog)s {unsee_dl_version}')
    parser.add_argument('-o', '--out', action="store", dest="out_dir", type=str, default=".",
                        help="Output directory")
    parser.add_argument('-v', '--verbose', action="store_const", dest="verbose", default=False, const=True,
                        help="Enable verbose output")
    parser.add_argument('-g', '--group', action="store_const", dest="group_album", default=False, const=True,
                        help="Group each album in its own directory")
    parser.add_argument('album_ids', action="store", nargs='+', help="unsee.cc album IDs to download")
    args = parser.parse_args(sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    # Download images
    album_ids = [get_album_id_from_url(url) for url in args.album_ids]
    album_ids_old_version = filter(lambda x: not is_beta_album_id(x), album_ids)
    album_ids_beta_version = filter(lambda x: is_beta_album_id(x), album_ids)

    async with Client(out_path=args.out_dir, group_album=args.group_album) as client:
        for album_id in album_ids_old_version:
            # noinspection PyBroadException
            try:
                print("Downloading album {:s}...".format(album_id))
                await client.download_album(album_id)
                logging.info("Download completed for album {}.".format(album_id))
            except Exception as ex:
                logging.error("Failed downloading album {}.".format(album_id), exc_info=ex)

    async with ClientBeta(out_path=args.out_dir, group_album=args.group_album) as client:
        await client.anonymous_login()

        for album_id in album_ids_beta_version:
            # noinspection PyBroadException
            try:
                print("Downloading album {:s}...".format(album_id))
                await client.download_album(album_id)
                logging.info("Download completed for album {}.".format(album_id))
            except Exception as ex:
                logging.error("Failed downloading album {}.".format(album_id), exc_info=ex)

    logging.shutdown()


if __name__ == '__main__':
    main()
