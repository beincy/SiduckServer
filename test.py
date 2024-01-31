from src.siduckserver import SiduckServer, DataFram
import asyncio

certificate = "cert.pem"
private_key = "key.pem"


async def hello(receiver, sender):
    d: DataFram = await receiver()
    print("got:", d.data)
    sender(b"world", True)


async def main():
    server = SiduckServer("127.0.0.1", "8083", certificate, private_key)
    server.set_request_handler(hello)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
