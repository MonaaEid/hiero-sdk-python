# read `TCK_PORT` (default 8544) and `TCK_HOST` (default
# localhost) from environment
# - Import and invoke server startup function
# - Add startup logging
# - Enable execution via `python -m hiero_sdk_python.tck`
import os
# from hiero_sdk_python.tck.server import start_tck_server
import logging
import asyncio

def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Read host and port from environment variables
    host = os.getenv('TCK_HOST', 'localhost')
    port = int(os.getenv('TCK_PORT', 8544))

    logger.info(f"Starting TCK server on {host}:{port}")

    # Start the TCK server
    # asyncio.run(start_tck_server(host, port))


if __name__ == "__main__":
    main()