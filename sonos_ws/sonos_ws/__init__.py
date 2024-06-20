import websockets
import asyncio
import json
from pprint import pp
import logging

logger = logging.getLogger(__name__)
handler = logging.NullHandler()
logger.addHandler(handler)

def to_ws_string(object):
    """Helper function to convert a Python dict to an object to pass to the HA Websockets API. For some reason, it must use double quotes."""
    return str(object).replace("'", "\"")


class SonosRoomState:
    def __init__(self, ws_new_state):
        """Create a SonosRoomState from a 'new_state' WS object."""
        try:
            self.id = ws_new_state['entity_id'][13:] # strip off 'media_player.' prefix
            self.name = ws_new_state['attributes']['friendly_name']
            self.state = ws_new_state['state']

            self.track = ws_new_state['attributes'].get('media_title')
            self.artist = ws_new_state['attributes'].get('media_artist')
            self.album = ws_new_state['attributes'].get('media_album_name')
            self.playlist = ws_new_state['attributes'].get('media_playlist')
            self.muted = ws_new_state['attributes'].get('is_volume_muted')
            self.shuffle = ws_new_state['attributes'].get('shuffle')
        except:
            logger.error(f"Error creating SonosRoomState for this input: {ws_new_state}")
            pass

    def __str__(self):
        return f"{self.name} [{self.id}]: {self.state} - {self.track} | {self.artist} | {self.album} | {self.playlist}"


async def connect(sock, access_token):
    auth_obj = {
        "type": "auth",
        "access_token": access_token
    }

    authreqd_message = await sock.recv()
    obj = json.loads(authreqd_message)
    logger.debug(f"Expecting auth_required, received {obj}")
    assert(obj['type'] == "auth_required")

    logger.debug(f"Sending auth message: {auth_obj}")
    await sock.send(to_ws_string(auth_obj))

    second_message = await sock.recv()
    obj = json.loads(second_message)
    logger.debug(f"Expecting auth_ok, received {obj}")
    assert(obj['type'] == "auth_ok")


async def subscribe(sock):
    event_sub = {
        "id": 1,
        "type": "subscribe_events",
        "event_type": "state_changed",
    }
    await sock.send(to_ws_string(event_sub))
    rsp = await sock.recv()
    obj = json.loads(rsp)
    assert(obj['type'] == "result" and obj['success'])


class SonosSubscription:
    def __init__(self):
        pass

    @classmethod
    async def create(cls, id, endpoint, access_token, callback):
        """Subscribe to events for a specific Sonos room"""
        self = cls()

        async with websockets.connect(f"ws://{endpoint}:8123/api/websocket") as sock:
            await connect(sock, access_token)
            await subscribe(sock)

            self.id = id
            logger.info(f"Subscribed to {self.id}")

            while True:
                msg = await sock.recv()
                obj = json.loads(msg)
                if obj['event']['data']['entity_id'].startswith('media_player'):
                    state = SonosRoomState(obj['event']['data']['new_state'])
                    logger.debug(f"New state: {state}")
                    if state.id == self.id:
                        logger.debug("Matched ID, calling callback")
                        callback(state)
