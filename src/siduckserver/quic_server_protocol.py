import asyncio
from aioquic.asyncio import QuicConnectionProtocol
from aioquic.quic.events import DatagramFrameReceived, ProtocolNegotiated, QuicEvent, StreamDataReceived
from typing import Dict, Callable, Coroutine, Any
from aioquic.quic.connection import QuicConnection


class DataFram:
    def __init__(self, data: bytes, end: bool = False) -> None:
        self.data = data
        self.end = end


class StreamHandler:
    def __init__(self, connection: QuicConnection, stream_id: int) -> None:
        self.connection = connection
        self.stream_id = stream_id
        self.queue: asyncio.Queue[DataFram] = asyncio.Queue()

    def set_event(self, event):
        self.queue.put_nowait(event)

    async def receiver(self, timeout: float = 0):
        if timeout:
            data = await asyncio.wait_for(self.queue.get(), timeout)
        else:
            data = await self.queue.get()
        return data

    def sender(self, data: bytes, end_stream: bool = False):
        self.connection.send_stream_data(self.stream_id, data, end_stream=end_stream)


class QuicServerProtocol(QuicConnectionProtocol):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._request_events: Dict[int, StreamHandler] = {}
        self._request_handler: Callable[
            [Callable[[], Coroutine[Any, Any, DataFram]], Callable[[bytes, bool], None]], bytes
        ] = None

    def set_request_handler(
        self,
        handler: Callable[[Callable[[], Coroutine[Any, Any, DataFram]], Callable[[bytes, bool], None]], bytes],
    ) -> None:
        self._request_handler = handler

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, ProtocolNegotiated):
            pass
        elif isinstance(event, DatagramFrameReceived):
            if event.data == b"quack":
                self._quic.send_datagram_frame(b"quack-ack")
        elif isinstance(event, StreamDataReceived):
            if event.stream_id not in self._request_events:
                self._request_events[event.stream_id] = StreamHandler(self._quic, event.stream_id)
                asyncio.create_task(
                    self._request_handler(
                        self._request_events[event.stream_id].receiver, self._request_events[event.stream_id].sender
                    )
                )
            if event.end_stream:
                self._request_events[event.stream_id].set_event(DataFram(event.data, True))
                self._request_events.pop(event.stream_id)
            else:
                self._request_events[event.stream_id].set_event(DataFram(event.data))
