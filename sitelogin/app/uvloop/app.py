# import asyncio
# import sys

# import uvloop

# async def main():
#     # Main entry-point.
#     ...

# if sys.version_info >= (3, 11):
#     with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
#         runner.run(main())
# else:
#     uvloop.install()
#     asyncio.run(main())


if __name__ == "__main__":
    config = uvicorn.Config(
        "app:app",
        log_level="debug",
        uds="/tmp/ecommerce.sock",
        reload=False,
        loop="uvloop",
        factory=False,
        workers=50,
    )
    server = uvicorn.Server(config)
    server.run()
