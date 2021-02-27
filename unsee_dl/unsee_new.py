import logging

import aiohttp

from unsee_dl.unsee_old import UnseeImage

DOMAIN = "unsee.cc"
_BASE_URL = f"https://{DOMAIN}"


class Client:
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

    async def anonymous_login(self, album_id):
        """
        Login with an anonymous token
        """
        url = f"{_BASE_URL}/auth?chat={album_id}"
        async with self.session.get(url) as response:
            content = await response.json()
            token = content["token"]
            self.token = token

    async def download_album(self, album_id):
        """
        Download an album from unsee betahttps://unsee.cc/image?id=ucGZtl0GozsxdrRf&size=small
        :param album_id: album id
        :type album_id: str
        """
        # problematic block generating invalid url error.
        # Fixed by dgndgn with patch 
        async for album_image in self._original_size_images(album_id):
            image = UnseeImage(
                album_id, album_image["id"], self.out_path, self.group_album
            )
            await self._download_and_save_image(image, _BASE_URL + "/" + album_image["urlBig"])

    async def _original_size_images(self, album_id):
        """
        Get original size image for the album
        :param album_id: unsee album id
        :type album_id: str
        :return: generator with each image in album
        :rtype: Generator
        """

        # await self._create_session(album_id)

        headers = {"authorization": f"Bearer {self.token}"}
        url = f"{_BASE_URL}/graphql"

        ql_body = """
query getAlbum($chat: ID!) {
  getAlbum(chat: $chat) {
    chat {
      ...ChatFragment
      __typename
    }
    images {
      ...ImageFragment
      __typename
    }
    sessions {
      ...SessionFragment
      __typename
    }
    messages {
      ...MessageFragment
      __typename
    }
    pins {
      ...PinFragment
      __typename
    }
    __typename
  }
}

fragment ChatFragment on Chat {
  id
  title
  ttl
  ttlLeft
  status
  description
  created
  allowDownloads
  allowUploads
  watermarkIp
  deleteAfter
  __typename
}

fragment ImageFragment on Image {
  id
  session
  chat
  created
  url(size: small)
  urlBig: url(size: big)
  hash
  width
  height
  priority
  __typename
}

fragment SessionFragment on Session {
  id
  role
  status
  chat
  online
  proxy
  created
  user
  name
  __typename
}

fragment MessageFragment on Message {
  id
  session
  recipient
  reply
  image
  pin
  text
  status
  created
  __typename
}

fragment PinFragment on Pin {
  id
  image
  session
  x
  y
  created
  __typename
}
"""
        body = {
            "operationName": "getAlbum",
            "query": ql_body,
            "variables": {
                "chat": album_id
            }
        }
        async with self.session.post(url, json=body, headers=headers) as response:
            content = await response.json()
            if "errors" in content and len(content["errors"]) > 0:
                raise Exception(content["errors"])

            album_items = content["data"]["getAlbum"]["images"]

            if not album_items or len(album_items) <= 0:
                print(f"No images found in album {album_id}")
                return

            print("Found album {} with {} images.".format(album_id, len(album_items)))

            for image in album_items:
                yield image

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
