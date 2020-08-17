import logging
from typing import AsyncIterable
from urllib.parse import urlparse

import aiohttp

from unsee_cc.unsee import UnseeImage


class UnseeCo:
    def __init__(self, session=None, out_path=".", group_album=True):
        """
        :param session: http session
        :type session: aiohttp.ClientSession
        :param out_path: output path
        :type out_path: str
        :param group_album: should images be grouped in folders per album
        :type group_album: bool
        """
        if session:
            self.session = session
        else:
            self.session = aiohttp.ClientSession()
        self.out_path = out_path
        self.group_album = group_album
        self.token = None

    async def __aenter__(self):
        self._did_enter_with = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and self._did_enter_with:
            await self.session.close()

    async def get_image_urls(self, album_id: str) -> AsyncIterable[str]:
        async with self.session.get(
            f"https://api.unsee.co/api/v1/getfile/{album_id}"
        ) as response:
            content = await response.json()
            if content["url"] == "not-found":
                raise Exception("album id not found")

            yield f"https://api.unsee.co/api/v1/getfile/uploads/{content['url']}"
            for url in content["otherUrls"] or []:
                yield f"https://api.unsee.co/api/v1/getfile/uploads/{url}"

    async def download_album(self, album_id: str):
        index = 0
        async for image_url in self.get_image_urls(album_id):
            image = UnseeImage(album_id, f"{index}", self.out_path, self.group_album)
            await self._download_and_save_image(image, image_url)
            index += 1

    async def _download_and_save_image(self, image, image_url):
        """
        Download and save the image
        :param image: unsee image
        :type image: UnseeImage
        :param image_url: image url
        :type image_url: str
        :return: saved image path
        :rtype: str
        """
        async with self.session.get(image_url) as response:
            image_path = await image.write_file_from_stream(response.content)
            logging.debug("Wrote image {}".format(image_path))

        return image_path


def get_album_id_from_url(album_url):
    url = urlparse(album_url)
    if url.netloc == "unsee.co":
        return url.path[1:]
    elif len(url.path) > 0:
        return url.path
    return None
