from __future__ import annotations

import queue
import sys
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import anyio
import mcp_types as types
from mcp.server.mcpserver import MCPServer
from mcp.shared.message import SessionMessage


@asynccontextmanager
async def _stdio_streams() -> AsyncIterator[tuple[Any, Any]]:
    """Crea streams MCP sobre stdin/stdout sin bloquear el event loop."""
    incoming_send, incoming_receive = anyio.create_memory_object_stream[SessionMessage | Exception](
        0
    )
    outgoing_send, outgoing_receive = anyio.create_memory_object_stream[SessionMessage](0)
    raw_lines: queue.Queue[bytes | None] = queue.Queue()

    def read_stdin() -> None:
        for line in sys.stdin.buffer:
            raw_lines.put(line)
        raw_lines.put(None)

    def write_stdout(message: SessionMessage) -> None:
        sys.stdout.write(message.message.model_dump_json(by_alias=True, exclude_unset=True))
        sys.stdout.write("\n")
        sys.stdout.flush()

    reader_thread = threading.Thread(target=read_stdin, name="sdlc-stdio-reader", daemon=True)
    reader_thread.start()

    async def feed_input() -> None:
        while True:
            try:
                line = raw_lines.get_nowait()
            except queue.Empty:
                await anyio.sleep(0.001)
                continue
            if line is None:
                break
            try:
                message = types.jsonrpc_message_adapter.validate_json(line, by_name=False)
            except Exception as error:
                await incoming_send.send(error)
            else:
                await incoming_send.send(SessionMessage(message))
        await incoming_send.aclose()

    async def drain_output() -> None:
        async with outgoing_receive:
            async for message in outgoing_receive:
                write_stdout(message)

    async with anyio.create_task_group() as task_group:
        task_group.start_soon(feed_input)
        task_group.start_soon(drain_output)
        try:
            yield incoming_receive, outgoing_send
        finally:
            task_group.cancel_scope.cancel()


async def run_stdio_async(server: MCPServer) -> None:
    """Ejecuta el transporte stdio con streams internos del SDK MCP."""
    async with _stdio_streams() as (read_stream, write_stream):
        lowlevel_server = server._lowlevel_server
        await lowlevel_server.run(
            read_stream,
            write_stream,
            lowlevel_server.create_initialization_options(),
        )


def run_stdio(server: MCPServer) -> None:
    """Inicia el transporte stdio del servidor MCP."""
    anyio.run(run_stdio_async, server)
