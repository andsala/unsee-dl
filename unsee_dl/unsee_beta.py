import logging

import aiohttp

from unsee_dl.unsee import UnseeImage

_GRAPHQL_URL = "https://api3.unsee.cc/graphql"


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

    async def anonymous_login(self):
        """
        Login with an anonymous token
        """
        gql_body = {
            "operationName": "getToken",
            "variables": {},
            "query": """
query getToken($identity: ID, $code: ID, $refreshToken: ID, $name: String) {
  getToken(identity: $identity, code: $code, refreshToken: $refreshToken, name: $name) {
    ...AuthPayloadFragment
    __typename
  }
}

fragment AuthPayloadFragment on AuthPayload {
  token
  refreshToken
  __typename
}
""",
        }
        async with self.session.post(_GRAPHQL_URL, json=gql_body) as response:
            content = await response.json()
            tokens = content["data"]["getToken"]
            self.token = tokens["token"]

    async def download_album(self, album_id):
        """
        Download an album from unsee beta
        :param album_id: album id
        :type album_id: str
        """
        async for album_image in self._original_size_images(album_id):
            image = UnseeImage(
                album_id, album_image["id"], self.out_path, self.group_album
            )
            await self._download_and_save_image(image, album_image["urlBig"])

    async def _create_session(self, album_id):
        # getSessions
        headers = {"authorization": f"Bearer {self.token}"}
        gql_body = {
            "operationName": "getSessions",
            "variables": {"filter": {"chat": album_id}},
            "query": """
query getSessions($filter: SessionFilter!, $pagination: Pagination) {
 getSessions(filter: $filter, pagination: $pagination) {
 ...SessionFragment
 __typename
 }
}

fragment SessionFragment on Session {
 id
 role
 status
 chat {
 ...ChatFragment
 __typename
 }
 online
 created
 viewing
 user
 name
 __typename
}

fragment ChatFragment on Chat {
 id
 title
 ttl
 ttlLeft
 status
 description
 created
 updated
 allowDownloads
 allowUploads
 watermarkIp
 deleteAfter
 __typename
}
""",
        }
        async with self.session.post(
            _GRAPHQL_URL, json=gql_body, headers=headers
        ) as response:
            content = await response.json()
            if "errors" in content and len(content["errors"]) > 0:
                raise Exception(content["errors"])

        # create session
        headers = {"authorization": f"Bearer {self.token}"}
        gql_body = {
            "operationName": "sessionCreate",
            "variables": {
                "input": {"chat": album_id, "referrer": "https://beta.unsee.cc/"}
            },
            "query": """
mutation sessionCreate($input: SessionCreateInput!) {
 sessionCreate(input: $input) {
 ...SessionFragment
 __typename
 }
}

fragment SessionFragment on Session {
 id
 role
 status
 chat {
 ...ChatFragment
 __typename
 }
 online
 created
 viewing
 user
 name
 __typename
}

fragment ChatFragment on Chat {
 id
 title
 ttl
 ttlLeft
 status
 description
 created
 updated
 allowDownloads
 allowUploads
 watermarkIp
 deleteAfter
 __typename
}
""",
        }
        async with self.session.post(
            _GRAPHQL_URL, json=gql_body, headers=headers
        ) as response:
            content = await response.json()
            if "errors" in content and len(content["errors"]) > 0:
                raise Exception(content["errors"])

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
        gql_body = {
            "operationName": "getAlbum",
            "variables": {"chat": album_id},
            "query": """
query getAlbum($chat: ID!) {
  getAlbum(chat: $chat) {
    images {
      ...ImageFragment
      __typename
    }
    __typename
  }
}

fragment ImageFragment on Image {
  id
  session
  created
  updated
  url(size: small)
  urlBig: url(size: big)
  hash
  __typename
}
""",
        }
        async with self.session.post(
            _GRAPHQL_URL, json=gql_body, headers=headers
        ) as response:
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
