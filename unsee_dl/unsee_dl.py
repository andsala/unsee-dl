import json
import logging
import ssl

import aiohttp
from aiohttp import WSMessage

from . import names
from .unsee import UnseeImage

_UNSEE_WEBSOCKET_URL = 'wss://ws.unsee.cc/{}/'


class Client:

    def __init__(self, session=None, out_path='.', group_album=True):
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

    async def download_album(self, album_id):
        unsee_name = names.get_random()
        ws_params = '?album={}&name={}'.format(album_id, unsee_name)
        ssl_context = ssl.create_default_context()

        # Settings WS
        async with self.session.ws_connect(_UNSEE_WEBSOCKET_URL.format('settings') + ws_params,
                                           ssl=ssl_context) as ws_settings:
            await ws_settings.send_str('{}')
            data = await ws_settings.receive()

            settings = json.loads(data.data, encoding='utf-8')

            logging.info('[ws_settings] {}'.format(settings))

        images_info = []

        # PubSub WS
        async with self.session.ws_connect(_UNSEE_WEBSOCKET_URL.format('pubsub') + ws_params,
                                           ssl=ssl_context) as ws_pubsub:
            data: WSMessage
            async for data in ws_pubsub:
                if data.type == aiohttp.WSMsgType.BINARY:
                    message = json.loads(data.data, encoding='utf-8')
                    logging.debug('[ws_pubsub] Received message: {}'.format(message))

                    if message['type'] == 'image':
                        images_info.append(message)
                        logging.info('[ws_pubsub] {}'.format(message))
                    else:
                        logging.debug('[ws_pubsub] Closing socket')
                        await ws_pubsub.close()
                elif data.type == aiohttp.WSMsgType.ERROR:
                    break

        logging.info('Found {} images in album {}'.format(len(images_info), album_id))
        if 'title' in settings and len(settings['title']) > 0:
            print('Found album "{}" ({}) with {} images.'.format(settings['title'], album_id, len(images_info)))
        else:
            print('Found album {} with {} images.'.format(album_id, len(images_info)))

        if len(images_info) <= 0:
            return

        # Imgpush WS
        async with self.session.ws_connect(_UNSEE_WEBSOCKET_URL.format('imgpush') + ws_params,
                                           ssl=ssl_context) as ws_imgpush:
            data: WSMessage
            async for data in ws_imgpush:
                logging.debug('[ws_imgpush] received image (len: {})'.format(len(data.data)))

                # noinspection PyBroadException
                try:
                    image = UnseeImage(album_id, out_path=self.out_path, group_album=self.group_album)
                    image_path = image.write_file_from_blob(data.data)
                    logging.debug('Wrote image {}'.format(image_path))

                    image_info = next(filter(lambda info: info['id'] == image.image_id, images_info), None)
                    if image_info is not None:
                        images_info.remove(image_info)
                except:
                    logging.warning('Failed writing image from album {}'.format(album_id))

                if len(images_info) <= 0:
                    await ws_imgpush.close()
