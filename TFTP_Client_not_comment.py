import socket
import argparse
from struct import pack

IP = 'localhost'
PORT = 69
TIMEOUT = 5
BLOCK_SIZE = 512
TRANSFER_MODE = 'octet'
OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
OPCODE_RE = {1:'RRQ', 2:'WRQ', 3:'DATA', 4:'ACK', 5:'ERROR'}
ERROR_CODE = {0: "정의되지 않은 오류", 1: "파일을 찾을 수 없음", 2: "액세스 위반", 3: "디스크가 꽉 찼거나 할당이 초과됨", 4: "잘못된 TFTP 작업", 5: "알 수 없는 전송의 ID", 6: "파일이 이미 존재함", 7: "해당 사용자가 없음"}

def send(filename, opcode, mode):
    format = f'>h{len(filename)}sB{len(mode)}sB'
    message = pack(format, opcode, bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(message, address)
    print(f"[send_{OPCODE_RE[opcode]}] message size : {len(message)}")
def send_ACK(seq_num, server):
    format = f'>hh'
    ack_message = pack(f'>hh', OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print(f"[send_ACK] seq_num : {seq_num}, message size : {len(ack_message)}")
def send_DATA(block_num, file_block, server):
    format = f'>hh{len(file_block)}s'
    data_message = pack(format, OPCODE['DATA'], block_num, file_block)
    sock.sendto(data_message, server)
    print(f"[send_DATA] num : {block_num}, message size : {len(data_message)}")

ps = argparse.ArgumentParser(description='TFTP client program')
ps.add_argument(dest="host", help="Server IP address", type=str)
ps.add_argument(dest="operation", help="get or put a file", type=str)
ps.add_argument(dest="filename", help="name of file to transfer", type=str)
ps.add_argument("-p", "--port", dest="port", type=int)
args = ps.parse_args()

if args.host:
    IP = args.host
    print("호스트 주소 변경이 성공적으로 되었습니다.")
if args.port:
    PORT = args.port
    print("포트 변경이 성공적으로 되었습니다.")

operation = str(args.operation).lower()
filename = args.filename
address = (IP, PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
type = 0

if operation == 'get':
    type = 1
elif operation == 'put':
    type = 2

if type < 1:
    print("'put'또는 'get'으로 입력하세요.")
    exit(0)

with open(filename, 'wb' if type == 1 else 'rb') as file:
    send(filename, OPCODE['RRQ'] if type == 1 else OPCODE['WRQ'], TRANSFER_MODE)

    if type == 2:
        sock.settimeout(TIMEOUT)

    expected_block_number = 1
    buf_size = 4

    if type == 1:
        buf_size += BLOCK_SIZE

    while True:
        try:
            data, server_socket = sock.recvfrom(buf_size)
            opcode = int.from_bytes(data[:2], 'big')
            block_number = int.from_bytes(data[2:4], 'big')
            print(f"[{OPCODE_RE[opcode]}] : block_num : {block_number}, data size : {len(data)}")

            if type == 1 and opcode == OPCODE['DATA']:
                if block_number == expected_block_number:
                    send_ACK(block_number, server_socket)
                    file_block = data[4:]
                    file.write(file_block)
                    expected_block_number = expected_block_number + 1
                    print(f"[file_block] size : {len(file_block)}")
                elif block_number > expected_block_number:
                    send_ACK(expected_block_number, server_socket)
                else:
                    send_ACK(block_number, server_socket)
            elif type == 2 and opcode == OPCODE['ACK']:
                if block_number < 1 or block_number == expected_block_number:
                    file_block = file.read(512)

                    if not file_block:
                        print("파일을 전부 보냈습니다.")
                        break

                    if block_number > 0:
                        expected_block_number += 1

                    send_DATA(expected_block_number, file_block, server_socket)
                else:
                    print("[BLOCK_NUMBER ERROR] 블럭 번호가 일치하지 않습니다!")
            elif opcode == OPCODE['ERROR']:
                error_code = int.from_bytes(data[2:4], byteorder='big')
                print(ERROR_CODE[error_code])
                break
            else:
                break
            if type == 1 and len(file_block) < BLOCK_SIZE:
                file.close()
                print("파일을 전부 받았습니다.")
                break
        except socket.timeout as e:
            print("Timeout!! : 타임 아웃되어 다시 보냅니다.")
            expected_block_number -= 1
            continue
file.close()