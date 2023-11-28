import socket
import argparse
from struct import pack

'''
$ tftp ip_address [-p port_mumber] <get|put> filename
'''

IP = 'localhost'
PORT = 69
TIMEOUT = 5
BLOCK_SIZE = 512
TRANSFER_MODE = 'octet'
OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
OPCODE_RE = {1:'RRQ', 2:'WRQ', 3:'DATA', 4:'ACK', 5:'ERROR'}
MODE = {'netascii': 1, 'octet': 2, 'mail': 3}
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

# argument에 host 데이터가 있으면 해당 데이터로 변경
if args.host:
    IP = args.host
    print("호스트 주소 변경이 성공적으로 되었습니다.")

# argument에 port 데이터가 있으면 해당 데이터로 변경
if args.port:
    PORT = args.port
    print("포트 변경이 성공적으로 되었습니다.")

# get 또는 put을 담는 변수
operation = str(args.operation).lower()

# 파일 이름을 담는 변수
filename = args.filename

# 서버 주소 변수
address = (IP, PORT)

# udp socket 생성
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# get 인지 put 인지 확인하는 변수
type = 0

# get 인지 put 인지 확인하는 조건문
if operation == 'get':
    type = 1
elif operation == 'put':
    type = 2

# get 또는 put이 아니면 종료.
if type < 1:
    print("'put'또는 'get'으로 입력하세요.")
    exit(0)

# get, put에 맞춰 파일을 읽거나 쓰기로 열기
with open(filename, 'wb' if type == 1 else 'rb') as file:
    # RRQ인지 WRQ인지 확인 후 메세지 보내기.
    send(filename, OPCODE['RRQ'] if type == 1 else OPCODE['WRQ'], TRANSFER_MODE)

    # WRQ이면 소켓에 타임 아웃 설정
    if type == 2:
        sock.settimeout(TIMEOUT)

    # 시작 기본 블럭 위치
    expected_block_number = 1

    # 기본 버퍼 사이즈
    buf_size = 4

    # RRQ일 때 데이터 블럭 사이즈 추가
    if type == 1:
        buf_size += BLOCK_SIZE

    while True:
        try:
            # udp 소켓으로 블럭을 받기
            data, server_socket = sock.recvfrom(buf_size)

            # opcode를 추출
            opcode = int.from_bytes(data[:2], 'big')

            # 데이터 블럭 번호
            block_number = int.from_bytes(data[2:4], 'big')

            # 데이터 블럭 번호, 데이터 사이즈 확인
            print(f"[{OPCODE_RE[opcode]}] : block_num : {block_number}, data size : {len(data)}")

            # RRQ 이고 OPCODE가 DATA일 때
            if type == 1 and opcode == OPCODE['DATA']:

                # 블럭 번호랑 예상 블럭 코드가 같을 때
                if block_number == expected_block_number:
                    # 블럭 코드와 예상 블럭 코드가 맞다면 ACK를 전송
                    send_ACK(block_number, server_socket)
                    # 4바이트 이후 데이터는 전부 File Block
                    file_block = data[4:]
                    # 파일에 File Block 입력
                    file.write(file_block)
                    # 다음 예상 블럭 코드 추가
                    expected_block_number = expected_block_number + 1
                    # File Block의 크기 출력
                    print(f"[file_block] size : {len(file_block)}")

                # 블럭 번호가 예상 블럭 코드보다 많을 때
                elif block_number > expected_block_number:
                    # 블럭 번호와 예상 블럭 코드가 안맞으면 다시 보내라고 ACK를 전송
                    send_ACK(expected_block_number, server_socket)
                else:
                    # 블럭 번호와 예상 블럭 코드가 안맞으면 다시 보내라고 ACK를 전송
                    send_ACK(block_number, server_socket)

            # WRQ 이고 OPCODE가 ACK일 때
            elif type == 2 and opcode == OPCODE['ACK']:
                # 블럭 번호가 0이거나 블럭 번호랑 예상 블럭 코드가 맞을 때
                if block_number < 1 or block_number == expected_block_number:
                    # file을 512바이트만큼 읽어오기
                    file_block = file.read(512)

                    # file을 읽어 왔는데 데이터가 비어있을 경우
                    if not file_block:
                        print("파일을 전부 보냈습니다.")
                        break

                    # 블럭 번호가 0 초과일 때 예상 블럭 코드를 1을 추가
                    if block_number > 0:
                        expected_block_number += 1

                    # 예상 블럭 코드와 파일 블럭을 보냄
                    send_DATA(expected_block_number, file_block, server_socket)
                else:
                    print("[BLOCK_NUMBER ERROR] 블럭 번호가 일치하지 않습니다!")

            # opcode가 ERROR일 때
            elif opcode == OPCODE['ERROR']:
                # Error code 추출
                error_code = int.from_bytes(data[2:4], byteorder='big')

                # Error 메세지 출력
                print(ERROR_CODE[error_code])
                break
            else:
                break

            # 파일 블럭 사이즈가 BLOCK_SIZE보다 작을 때 탈출
            if type == 1 and len(file_block) < BLOCK_SIZE:
                file.close()
                print("파일을 전부 받았습니다.")
                break
        # 타임 아웃 예외 처리
        except socket.timeout as e:
            print("Timeout!! : 타임 아웃되어 다시 보냅니다.")
            expected_block_number -= 1
            continue

file.close()
