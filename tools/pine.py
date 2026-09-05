#!/usr/bin/env python3
"""Talk to a running PCSX2 over PINE, its IPC socket.

This is the project's equivalent of a debug console: read and write emulated
PS2 memory, query what is running, and drive save states -- all from a
script, with no OS-level screen capture or synthetic keystrokes.

Enable it once in PCSX2.ini:

    [EmuCore]
    EnablePINE = true
    PINESlot = 28011

PCSX2 then listens on a unix socket at $TMPDIR/pcsx2.sock (macOS/Linux).

Protocol: request is <u32 total_len><u8 opcode><args>, reply is
<u32 total_len><u8 result><data>, result 0 = OK. Integers little-endian.
"""
import os
import socket
import struct
import tempfile

# opcodes
READ8, READ16, READ32, READ64 = 0x00, 0x01, 0x02, 0x03
WRITE8, WRITE16, WRITE32, WRITE64 = 0x04, 0x05, 0x06, 0x07
VERSION, SAVESTATE, LOADSTATE = 0x08, 0x09, 0x0A
TITLE, GAMEID, UUID, GAMEVERSION, STATUS = 0x0B, 0x0C, 0x0D, 0x0E, 0x0F


class PineError(RuntimeError):
    pass


class Pine:
    def __init__(self, path=None, timeout=10.0):
        self.path = path or os.path.join(
            tempfile.gettempdir(), "pcsx2.sock")
        self.timeout = timeout

    def _call(self, payload):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(self.timeout)
            try:
                s.connect(self.path)
            except (FileNotFoundError, ConnectionRefusedError) as e:
                raise PineError(
                    f"no PCSX2 listening at {self.path} ({e}); is it running "
                    f"with EnablePINE=true?") from e
            msg = struct.pack("<I", 4 + len(payload)) + payload
            s.sendall(msg)
            head = self._recv_exact(s, 4)
            total = struct.unpack("<I", head)[0]
            body = self._recv_exact(s, total - 4)
        if not body or body[0] != 0:
            raise PineError(f"PINE returned failure for opcode {payload[0]:#x}")
        return body[1:]

    @staticmethod
    def _recv_exact(s, n):
        buf = b""
        while len(buf) < n:
            chunk = s.recv(n - len(buf))
            if not chunk:
                raise PineError("PINE closed the connection early")
            buf += chunk
        return buf

    # --- memory -----------------------------------------------------------
    def read8(self, addr):
        return self._call(struct.pack("<BI", READ8, addr))[0]

    def read32(self, addr):
        return struct.unpack("<I", self._call(struct.pack("<BI", READ32, addr)))[0]

    def read(self, addr, length):
        """Bulk read. PINE has no block-read opcode, so this batches many
        32-bit reads into one connection -- far faster than one call each."""
        out = bytearray()
        CHUNK = 512                      # requests per round trip
        pos = 0
        while pos < length:
            n = min(CHUNK, (length - pos + 3) // 4)
            payload = b"".join(struct.pack("<BI", READ32, addr + pos + i * 4)
                               for i in range(n))
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect(self.path)
                for i in range(n):
                    one = payload[i * 5:(i + 1) * 5]
                    s.sendall(struct.pack("<I", 4 + len(one)) + one)
                    head = self._recv_exact(s, 4)
                    total = struct.unpack("<I", head)[0]
                    body = self._recv_exact(s, total - 4)
                    if body[0] != 0:
                        raise PineError("read failed")
                    out += body[1:5]
            pos += n * 4
        return bytes(out[:length])

    def write8(self, addr, val):
        self._call(struct.pack("<BIB", WRITE8, addr, val & 0xFF))

    def write(self, addr, data):
        for i, b in enumerate(data):
            self.write8(addr + i, b)

    # --- status -----------------------------------------------------------
    def _string(self, opcode):
        d = self._call(struct.pack("<B", opcode))
        n = struct.unpack("<I", d[:4])[0]
        return d[4:4 + n].rstrip(b"\x00").decode("utf-8", "replace")

    def version(self):
        return self._string(VERSION)

    def title(self):
        return self._string(TITLE)

    def game_id(self):
        return self._string(GAMEID)

    def game_version(self):
        return self._string(GAMEVERSION)

    def status(self):
        return struct.unpack("<I", self._call(struct.pack("<B", STATUS)))[0]

    def save_state(self, slot):
        self._call(struct.pack("<BB", SAVESTATE, slot))

    def load_state(self, slot):
        self._call(struct.pack("<BB", LOADSTATE, slot))


if __name__ == "__main__":
    p = Pine()
    print("version     :", p.version())
    print("title       :", p.title())
    print("game id     :", p.game_id())
    print("game version:", p.game_version())
    print("status      :", p.status())
