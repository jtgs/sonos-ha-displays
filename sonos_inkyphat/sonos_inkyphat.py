import sonos_ws
import asyncio
import logging
import argparse


def callback(state):
    logging.debug("In callback")
    logging.info(state.track)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("room", help="ID of the Sonos room to watch")
    parser.add_argument("endpoint", help="IP or DNS name of Home Assistant server")
    parser.add_argument("access_token", help="Home Assistant access token")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        default=logging.INFO,
        help="enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        format="%(asctime)s - %(name)20s - %(funcName)30s - %(levelname)5s - %(message)s",
        level=args.loglevel,
    )

    logging.info(f"Subscribing to {args.room} at {args.endpoint}")
    sub = await sonos_ws.SonosSubscription.create(
        args.room, args.endpoint, args.access_token, callback
    )


if __name__ == "__main__":
    asyncio.run(main())
