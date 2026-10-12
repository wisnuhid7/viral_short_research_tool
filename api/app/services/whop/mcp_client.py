"""Whop MCP stdio client.

Port of server/src/services/whop/whop-mcp-client.ts.

Spawns `npx -y mcp-remote https://mcp.whop.com/mcp`, performs the JSON-RPC
handshake (initialize id=1), calls the `bounties_list` tool (id=2), and returns
the parsed bounty list. Overall timeout: 30s.
"""
import asyncio
import json
import uuid

WHOP_MCP_URL = "https://mcp.whop.com/mcp"
TIMEOUT_MS = 30000


async def _drive(proc: asyncio.subprocess.Process, first: int, intent_id: str) -> list[dict]:
    buffer = ""
    while True:
        chunk = await proc.stdout.read(4096)  # type: ignore[union-attr]
        if not chunk:
            raise RuntimeError(f"Whop MCP proxy exited with code {proc.returncode}")
        buffer += chunk.decode("utf-8", "replace")

        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
            except ValueError:
                # Ignore non-JSON lines (e.g. logging)
                continue

            # 1. Handshake: initialized -> issue tools/call
            if msg.get("id") == 1:
                call_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "bounties_list",
                        "arguments": {
                            "status": "open",
                            "first": first,
                            "intent": "Sinkronisasi campaign Whop Content Rewards",
                            "intent_id": intent_id,
                        },
                    },
                }
                proc.stdin.write((json.dumps(call_payload) + "\n").encode())  # type: ignore[union-attr]
                await proc.stdin.drain()  # type: ignore[union-attr]
            # 2. Result of tools/call
            elif msg.get("id") == 2:
                if msg.get("error"):
                    err = msg["error"]
                    raise RuntimeError(
                        f"Whop MCP RPC Error: {err.get('message') or json.dumps(err)}"
                    )

                content = (msg.get("result") or {}).get("content") or []
                text = content[0].get("text") if content else None
                if not text:
                    raise RuntimeError("Format balasan dari Whop MCP tidak sesuai harapan (kosong).")

                try:
                    parsed = json.loads(text)
                except ValueError as json_err:
                    raise RuntimeError(f"Gagal mem-parse JSON hasil bounties Whop: {json_err}") from json_err

                return parsed.get("data") or []


async def fetch_whop_bounties_from_mcp(first: int = 50) -> list[dict]:
    """Execute a call to the Whop MCP Server via the stdio proxy (mcp-remote)."""
    intent_id = str(uuid.uuid4())

    try:
        proc = await asyncio.create_subprocess_exec(
            "npx",
            "-y",
            "mcp-remote",
            WHOP_MCP_URL,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except OSError as err:
        raise RuntimeError(f"Gagal menjalankan proses Whop MCP proxy: {err}") from err

    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "viral-short-research-sync", "version": "1.0.0"},
        },
    }

    try:
        proc.stdin.write((json.dumps(init_req) + "\n").encode())  # type: ignore[union-attr]
        await proc.stdin.drain()  # type: ignore[union-attr]
        return await asyncio.wait_for(_drive(proc, first, intent_id), timeout=TIMEOUT_MS / 1000)
    except asyncio.TimeoutError as err:
        raise RuntimeError(
            f"Timeout ({TIMEOUT_MS}ms) saat menyinkronkan data dengan Whop MCP server"
        ) from err
    finally:
        if proc.returncode is None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            await proc.wait()
