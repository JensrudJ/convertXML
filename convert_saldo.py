"""
Download Saldoliste XML from FTP, convert to tab-separated txt (partno, baltot),
and upload the result back to the same FTP.

Usage:
    python convert_saldo.py
    python convert_saldo.py --filename Saldoliste   (override remote filename)
"""

import argparse
import ftplib
import io
import logging
import os
import xml.etree.ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "convert_saldo.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

FTP_HOST = "edi.sr-transport.no"
FTP_PORT = 21
FTP_USER = "36309"
FTP_PASS = "Avirket-Rottene-Tinningen2"

DEFAULT_FILENAME = "Saldoliste"
OUTPUT_FILENAME = "saldofil.txt"


def download_from_ftp(ftp, filename):
    buf = io.BytesIO()
    ftp.retrbinary(f"RETR {filename}", buf.write)
    buf.seek(0)
    return buf.read()


def upload_to_ftp(ftp, filename, data):
    buf = io.BytesIO(data)
    ftp.storbinary(f"STOR {filename}", buf)


def convert_xml_to_tsv(xml_bytes):
    root = ET.fromstring(xml_bytes)
    lines = []
    for artikkel in root.findall("Artikkel"):
        partno = artikkel.findtext("partno", "").strip()
        baltot_raw = artikkel.findtext("baltot", "0")
        baltot = int(float(baltot_raw))
        lines.append(f"{partno}\t{baltot}")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Convert Saldoliste XML to flat TSV")
    parser.add_argument("--filename", default=DEFAULT_FILENAME,
                        help=f"Remote filename to download (default: {DEFAULT_FILENAME})")
    args = parser.parse_args()

    try:
        log.info("Connecting to %s...", FTP_HOST)
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        log.info("Connected.")

        ftp.cwd("ISANORGE")

        log.info("Downloading %s...", args.filename)
        xml_bytes = download_from_ftp(ftp, args.filename)
        log.info("Downloaded %d bytes.", len(xml_bytes))

        tsv_text = convert_xml_to_tsv(xml_bytes)
        row_count = tsv_text.count("\n")
        log.info("Converted %d rows.", row_count)

        log.info("Uploading %s...", OUTPUT_FILENAME)
        upload_to_ftp(ftp, OUTPUT_FILENAME, tsv_text.encode("utf-8"))
        log.info("Done — %d rows uploaded.", row_count)

        ftp.quit()
    except Exception:
        log.exception("Run failed")


if __name__ == "__main__":
    main()
