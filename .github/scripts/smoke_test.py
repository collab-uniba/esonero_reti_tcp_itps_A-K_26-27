#!/usr/bin/env python3
"""Smoke test for the currency converter assignment.

Checks the student client and server against a reference implementation of
the application protocol, using the examples in Assegnazione.md. Passing this test
does NOT guarantee a pass in the final grading, which uses further cases.

Usage: smoke_test.py CLIENT_EXE SERVER_EXE
"""

import os
import select
import socket
import struct
import subprocess
import sys
import tempfile
import time
from decimal import Decimal

HOST = "127.0.0.1"
DEFAULT_PORT = 56700
REF_PORT = 56701
CLOSED_PORT = 56702
TIMEOUT = 5
MAX_AMOUNT = 10000000
PREFIX = "Ricevuto risultato dal server ip 127.0.0.1. "

RATES = {
    "EUR": 10000, "USD": 10850, "GBP": 8550, "CHF": 9450,
    "JPY": 1620000, "CAD": 14800, "AUD": 16500, "CNY": 78000,
}

# (-r argument, expected client output after PREFIX, expected server log)
CASES = [
    ("EUR USD 100", "100.00 EUR = 108.50 USD", "Richiesta 'EUR USD 100.00' dal client ip 127.0.0.1"),
    ("eur usd 100.5", "100.50 EUR = 109.04 USD", "Richiesta 'eur usd 100.50' dal client ip 127.0.0.1"),
    ("USD EUR 100", "100.00 USD = 92.17 EUR", "Richiesta 'USD EUR 100.00' dal client ip 127.0.0.1"),
    ("GBP JPY 1000", "1000.00 GBP = 189473.68 JPY", "Richiesta 'GBP JPY 1000.00' dal client ip 127.0.0.1"),
    ("JPY EUR 5000", "5000.00 JPY = 30.86 EUR", "Richiesta 'JPY EUR 5000.00' dal client ip 127.0.0.1"),
    ("CHF CHF 12.34", "12.34 CHF = 12.34 CHF", "Richiesta 'CHF CHF 12.34' dal client ip 127.0.0.1"),
    ("EUR USD 100000", "100000.00 EUR = 108500.00 USD", "Richiesta 'EUR USD 100000.00' dal client ip 127.0.0.1"),
    ("EUR XYZ 10", "Valuta non supportata", "Richiesta 'EUR XYZ 10.00' dal client ip 127.0.0.1"),
    ("XYZ USD 0", "Valuta non supportata", "Richiesta 'XYZ USD 0.00' dal client ip 127.0.0.1"),
    ("EUR USD 0", "Importo non valido", "Richiesta 'EUR USD 0.00' dal client ip 127.0.0.1"),
    ("EUR USD 100000.01", "Importo non valido", "Richiesta 'EUR USD 100000.01' dal client ip 127.0.0.1"),
]

USAGE_CASES = ["EURO USD 10", "EUR USD 1.234", "EUR USD 10,50", "EUR USD -5", "EUR USD"]

BYTE_ORDER_HINT = "sembra un errore di byte order: hai usato htonl()/ntohl()?"

results = []  # (section, name, ok, detail)


def check(section, name, ok, detail=""):
    results.append((section, name, ok, detail))
    print("[%s] %s: %s%s" % ("OK" if ok else "FAIL", section, name, "" if ok else " -> " + detail))


def parse_request(req):
    frm, to, amount = req.split(" ")
    return frm, to, int(Decimal(amount) * 100)


def reference_response(frm, to, amount):
    rate_from, rate_to = RATES.get(frm.upper()), RATES.get(to.upper())
    if rate_from is None or rate_to is None:
        return 1, 0
    if amount == 0 or amount > MAX_AMOUNT:
        return 2, 0
    return 0, (amount * rate_to + rate_from // 2) // rate_from


def recv_exactly(sock, n):
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            break
        data += chunk
    return data


def normalize(out):
    return out.decode("utf-8", errors="replace").replace("\r\n", "\n").rstrip("\n")


def executable(path):
    path = os.path.abspath(path)
    if os.name == "nt" and not path.lower().endswith(".exe"):
        path += ".exe"
    return path


def run_client(client, args):
    try:
        proc = subprocess.run([client] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              stdin=subprocess.DEVNULL, timeout=TIMEOUT)
        return proc.returncode, normalize(proc.stdout), None
    except subprocess.TimeoutExpired:
        return None, "", "il client non termina entro %d s" % TIMEOUT
    except OSError as e:
        return None, "", "impossibile eseguire il client: %s" % e


def connect_with_retry(port):
    deadline = time.time() + TIMEOUT
    while True:
        try:
            return socket.create_connection((HOST, port), timeout=TIMEOUT)
        except ConnectionRefusedError:
            if time.time() > deadline:
                raise
            time.sleep(0.2)


def test_server(server, client):
    section = "server"
    log = tempfile.TemporaryFile()
    try:
        proc = subprocess.Popen([server], stdout=log, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    except OSError as e:
        check(section, "avvio", False, "impossibile eseguire il server: %s" % e)
        return
    time.sleep(1)
    if proc.poll() is not None:
        check(section, "avvio", False, "il server termina subito (exit code %s)" % proc.returncode)
        return
    check(section, "avvio", True)

    expected_log = []
    for req, _, log_line in CASES:
        frm, to, amount = parse_request(req)
        payload = struct.pack("!4s4sI", frm.encode(), to.encode(), amount)
        name = "risposta a '%s'" % req
        try:
            with connect_with_retry(DEFAULT_PORT) as sock:
                sock.sendall(payload)
                data = recv_exactly(sock, 8)
        except OSError as e:
            check(section, name, False, "errore di comunicazione sulla porta %d: %s (verifiche "
                  "successive sul server saltate)" % (DEFAULT_PORT, e))
            break
        expected_log.append(log_line)
        if len(data) != 8:
            check(section, name, False, "ricevuti %d byte invece di 8" % len(data))
            continue
        got = struct.unpack("!II", data)
        expected = reference_response(frm, to, amount)
        if got == expected:
            check(section, name, True)
        else:
            detail = "status/amount = %s, attesi %s" % (got, expected)
            status_le = struct.unpack("<I", data[0:4])[0]
            if struct.unpack("<II", data) == expected or (got[0] > 2 and status_le <= 2):
                detail += "; " + BYTE_ORDER_HINT
            check(section, name, False, detail)

    # End-to-end: student client against student server, default address and port
    code, out, err = run_client(client, ["-r", "EUR USD 100"])
    expected_out = PREFIX + "100.00 EUR = 108.50 USD"
    if err:
        check("end-to-end", "client e server con parametri di default", False, err)
    else:
        expected_log.append(CASES[0][2])
        check("end-to-end", "client e server con parametri di default", code == 0 and out == expected_out,
              "exit code %s, output %r, atteso %r" % (code, out, expected_out))

    proc.terminate()
    try:
        proc.wait(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
    log.seek(0)
    lines = normalize(log.read()).split("\n")
    missing = [line for line in expected_log if line not in lines]
    check(section, "log delle richieste", not missing,
          "righe mancanti o diverse, ad es. %r (righe stampate: %r). Se non stampa nulla, "
          "chiama fflush(stdout) dopo ogni printf" % (missing[0] if missing else "", lines[:3]))


def serve_reference(conn):
    """Read one request and reply as the reference server. Returns the raw request."""
    with conn:
        conn.settimeout(TIMEOUT)
        data = recv_exactly(conn, 12)
        if len(data) == 12:
            frm = data[0:4].split(b"\0")[0].decode("ascii", errors="replace")
            to = data[4:8].split(b"\0")[0].decode("ascii", errors="replace")
            amount = struct.unpack("!I", data[8:12])[0]
            conn.sendall(struct.pack("!II", *reference_response(frm, to, amount)))
        return data


def client_vs_reference(client, args, listener):
    """Run the client against the reference server.

    Returns (exit code, stdout, raw request or None if no connection, error).
    """
    try:
        proc = subprocess.Popen([client] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                stdin=subprocess.DEVNULL)
    except OSError as e:
        return None, "", None, "impossibile eseguire il client: %s" % e
    request, error = None, None
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        exited = proc.poll() is not None
        if select.select([listener], [], [], 0.3 if exited else 0.1)[0]:
            try:
                request = serve_reference(listener.accept()[0])
            except OSError as e:
                request, error = b"", "errore di comunicazione: %s" % e
            break
        if exited:
            break
    try:
        out, _ = proc.communicate(timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        return None, "", request, "il client non termina entro %d s" % TIMEOUT
    return proc.returncode, normalize(out), request, error


def check_request(data, frm, to, amount):
    if data is None:
        return "nessuna richiesta ricevuta"
    if len(data) != 12:
        return "ricevuti %d byte invece di 12" % len(data)
    if data[3:4] != b"\0" or data[7:8] != b"\0":
        return "i campi from/to devono terminare con '\\0' (byte 3 e 7)"
    if data[0:3].decode("ascii", "replace").upper() != frm.upper() or \
            data[4:7].decode("ascii", "replace").upper() != to.upper():
        return "valute ricevute %r, attese %r" % ((data[0:3], data[4:7]), (frm, to))
    got = struct.unpack("!I", data[8:12])[0]
    if got != amount:
        detail = "amount ricevuto %d, atteso %d" % (got, amount)
        if struct.unpack("<I", data[8:12])[0] == amount:
            detail += "; " + BYTE_ORDER_HINT
        return detail
    return None


def test_client(client):
    section = "client"
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if os.name != "nt":  # on Windows SO_REUSEADDR allows port hijacking
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind((HOST, REF_PORT))
    listener.listen(5)
    port_args = ["-s", HOST, "-p", str(REF_PORT)]

    for req, expected_out, _ in CASES:
        frm, to, amount = parse_request(req)
        name = "output per '%s'" % req
        code, out, request, err = client_vs_reference(client, port_args + ["-r", req], listener)
        if err:
            check(section, name, False, err)
            continue
        if request is None:
            check(section, name, False, "il client non si connette al server")
            continue
        problem = check_request(request, frm, to, amount)
        if problem:
            check(section, name, False, "richiesta errata: " + problem)
            continue
        expected_out = PREFIX + expected_out
        check(section, name, code == 0 and out == expected_out,
              "exit code %s, output %r, atteso %r" % (code, out, expected_out))

    for req in USAGE_CASES:
        name = "argomenti non validi '%s'" % req
        code, out, request, err = client_vs_reference(client, port_args + ["-r", req], listener)
        if err:
            check(section, name, False, err)
        else:
            check(section, name, code != 0 and request is None,
                  "atteso exit code != 0 e nessuna connessione (exit code %s, connessione: %s)"
                  % (code, "no" if request is None else "si"))
    listener.close()

    code, out, err = run_client(client, ["-s", HOST, "-p", str(CLOSED_PORT), "-r", "EUR USD 100"])
    check(section, "server non raggiungibile", not err and code != 0 and not out.startswith(PREFIX),
          err or "atteso exit code != 0 (exit code %s, output %r)" % (code, out))


def write_summary():
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write("## Smoke test\n\n| Esito | Area | Verifica | Dettaglio |\n|---|---|---|---|\n")
        for section, name, ok, detail in results:
            f.write("| %s | %s | %s | %s |\n" % ("✅" if ok else "❌", section, name.replace("|", "\\|"),
                                               "" if ok else detail.replace("|", "\\|")))
        f.write("\n> Il superamento dello smoke test non garantisce il superamento della correzione finale.\n")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    client, server = executable(sys.argv[1]), executable(sys.argv[2])
    test_client(client)
    test_server(server, client)
    write_summary()
    failed = sum(1 for r in results if not r[2])
    print("\n%d verifiche, %d fallite" % (len(results), failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
