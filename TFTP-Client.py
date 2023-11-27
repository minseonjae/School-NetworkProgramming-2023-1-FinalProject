import socket
import argparse
from struct import pack

DEFAULT = {'PORT': 69, 'BLOCK_SIZE':512, 'TRANSFER_MODE':'octet'}
OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}
ERROR_CODE = {
    0: "Not defined, see error message (if any).",
    1: "File not found.",
    2: "Access violation.",
    3: "Disk full or allocation exceeded.",
    4: "Illegal TFTP operation.",
    5: "Unknown transfer ID.",
    6: "File already exists.",
    7: "No such user."
}

ps = argparse.ArgumentParser(description='TFTP client program')
ps.add_argument(dest="host", help="Server IP address", type=str)
ps.add_argument(dest="operation", help="get or put a file", type=str)
ps.add_argument(dest="filename", help="name of file to transfer", type=str)
ps.add_argument("-p", "--port", dest="port", type=int)
args = ps.parse_args()