import asyncio
from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from .quic_server_protocol import QuicServerProtocol, DataFram
from typing import Callable, Coroutine, Any


class SiduckServer:
    def __init__(self, host: str, port: str, certificate: str, private_key: str, **kwargs):
        """
        host: host of server
        port: port of server
        certificate: path of certificate file. If not set, no certificate will be used.
        private_key: path of private key file. If not set, no private key will be used.
        kwargs: attrs of aioquic.quic.configuration.QuicConfiguration
        """
        self.host = host
        self.port = port
        self.configuration = QuicConfiguration(alpn_protocols=["siduck"], is_client=False, **kwargs)
        self.configuration.load_cert_chain(certificate, private_key)
        self.handler = None

    def set_request_handler(
        self,
        handler: Callable[[Callable[[], Coroutine[Any, Any, DataFram]], Callable[[bytes, bool], None]], bytes],
    ):
        """
        set handler for request.
        """
        self.handler = handler

    async def start(self):
        """
        listen
        """

        def create_protocol(*args, **kwargs):
            protocol = QuicServerProtocol(*args, **kwargs)
            protocol.set_request_handler(self.handler)
            return protocol

        await serve(self.host, self.port, configuration=self.configuration, create_protocol=create_protocol)
        print(f"listen at {self.host}:{self.port}")
        await asyncio.Future()


__all__ = ["SiduckServer", "DataFram"]
