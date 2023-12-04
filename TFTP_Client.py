import socket
import argparse
from struct import pack

# python tftp_client.py <server_ip> <operation_type> <filename> [-p PORT]

TIME_OUT = 5  # 타임 아웃 시간 설정 변수
TRANSFER_MODE = 'octet'  # 전송 모드 설정 변수
BLOCK_SIZE = 512  # 데이터 블럭 사이즈 설정 변수
OPCODE = {'RRQ': 1, 'WRQ': 2, 'DATA': 3, 'ACK': 4, 'ERROR': 5}
OPCODE_RE = {1: 'RRQ', 2: 'WRQ', 3: 'DATA', 4: 'ACK', 5: 'ERROR'}
# MODE = {'netascii': 1, 'octet': 2, 'mail': 3} 사용하지 않는 코드
ERROR_CODE = {0: "정의되지 않은 오류", 1: "파일을 찾을 수 없음", 2: "액세스 위반", 3: "디스크가 꽉 찼거나 할당이 초과됨", 4: "잘못된 TFTP 작업", 5: "알 수 없는 전송의 ID", 6: "파일이 이미 존재함", 7: "해당 사용자가 없음"}

# WRQ 또는 RRQ 블럭을 전송하기 위한 함수
def send(filename, opcode, mode):
    message = pack(f'>h{len(filename)}sB{len(mode)}sB', opcode, bytes(filename, 'utf-8'), 0, bytes(mode, 'utf-8'), 0)
    sock.sendto(message, address)
    print(f"[send_{OPCODE_RE[opcode]}] message size : {len(message)}")

# ACK 블럭을 전송하기 위한 함수
def send_ACK(seq_num, server):
    ack_message = pack(f'>hh', OPCODE['ACK'], seq_num)
    sock.sendto(ack_message, server)
    print(f"[send_ACK] seq_num : {seq_num}, message size : {len(ack_message)}")

# DATA 블럭을 보내기 위한 함수
def send_DATA(block_num, file_block, server):
    data_message = pack(f'>hh{len(file_block)}s', OPCODE['DATA'], block_num, file_block)
    sock.sendto(data_message, server)
    print(f"[send_DATA] num : {block_num}, message size : {len(data_message)}")

# 실행 시에 커맨드 라인 인수를 받을 때 사용
ps = argparse.ArgumentParser(description='TFTP client program')
ps.add_argument(dest="host", help="Server IP address", type=str)
ps.add_argument(dest="operation", help="get or put a file", type=str)
ps.add_argument(dest="filename", help="name of file to transfer", type=str)
ps.add_argument("-p", "--port", dest="port", type=int)

args = ps.parse_args()  # 커멘드 라인 인수 받음
operation = str(args.operation).lower()  # 전송 모드인 get 또는 put을 받는 변수
type = 1 if operation == 'get' else (2 if operation == 'put' else 0)  # 전송 모드가 get 또는 put 인지 확인하여 정수로 바꾸는 삼항 연산자가 들어간 변수

# get 또는 put이 아니면 종료
if type < 1:
    print("'put'또는 'get'으로 입력하세요.")
    exit(0)

ip = args.host if args.host else 'localhost'  # 서버의 ip 변수 : host 인수가 있을 경우 인수로 데이터로 바꾸고 아니면 기본 데이터 'localhost'로 설정
port = args.port if args.port else 69  # 서버의 port 변수 : port 인수가 있을 경우 인수로 데이터를 바꾸고 아니면 기본 데이터 69로 설정
address = (ip, port)  # 서버 주소 변수
filename = args.filename  # 인수에서 파일 이름을 받아오는 변수
expected_block_number = 1  # 시작 예상 블럭 번호 변수
buf_size = 4 + (BLOCK_SIZE if type == 1 else 0)  # 전송 모드의 get 또는 put 인지 확인하여 버퍼 사이즈를 바꾸는 삼항 연산자가 들어간 변수

print(f"[START] {operation}모드로 작동을 시작합니다.")

# UDP 소켓 생성, 어떤 오류가 발생하더라도 안전하게 닫히도록 with 문 사용
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    # 파일을 읽거나 쓰는 file 변수 생성, 어떤 오류가 발생하더라도 안전하게 닫히도록 with 문 사용
    with open(filename, 'wb' if type == 1 else 'rb') as file:
        # 'get'이면 'RRQ'로 'put'이면 'WRQ'로 확인 후 메세지 블럭 보냄
        send(filename, OPCODE['RRQ' if type == 1 else 'WRQ'], TRANSFER_MODE)

        # 'put'인 경우 타임 아웃을 설정
        if type == 2:
            sock.settimeout(TIME_OUT)

        while True:
            try:
                # UDP 소켓으로 블럭을 받기
                data, server_socket = sock.recvfrom(buf_size)

                # 받은 블럭에서 opcode를 추출
                opcode = int.from_bytes(data[:2], 'big')

                # 받은 블럭에서 블럭 번호를 추출
                block_number = int.from_bytes(data[2:4], 'big')

                print(f"[{OPCODE_RE[opcode]}] : block_num : {block_number}, data size : {len(data)}")

                # 'get'이고 opcode가 DATA일 때
                if type == 1 and opcode == OPCODE['DATA']:
                    # 블럭 번호와 예상 블럭 코드가 같을 떄
                    if block_number == expected_block_number:
                        # ACK 블럭을 전송
                        send_ACK(block_number, server_socket)

                        # 4바이트 이후 데이터를 파일 데이터로 변환
                        file_block = data[4:]

                        # 파일에 파일 데이터를 파일에 쓰기
                        file.write(file_block)

                        # 예상 블럭 코드 추가
                        expected_block_number = expected_block_number + 1

                        print(f"[FILE BLOCK] size : {len(file_block)}")

                        # 파일 블럭의 크기가 BLOCK_SIZE보다 작을 때
                        if len(file_block) < BLOCK_SIZE:
                            print("[END] 파일을 전부 받았습니다.")
                            break
                    # 파일 블럭 번호가 예상 파일 블럭 번호보다 많을 때
                    elif block_number > expected_block_number:
                        # 예상 파일 블럭 번호의 파일 번호를 보내라고 ACK 블럭을 전송
                        send_ACK(expected_block_number, server_socket)
                    else:
                        # 파일 블럭 번호의 파일 번호를 보내라고 ACK 블럭을 전송
                        send_ACK(block_number, server_socket)
                # 'put'이고 opcode가 ACK일 때
                elif type == 2 and opcode == OPCODE['ACK']:
                    # 블럭 번호가 0이거나 블럭 번호랑 예상 블럭 코드가 맞을 때
                    if block_number < 1 or block_number == expected_block_number:
                        # 파일을 512바이트 만큼 불러와서 파일 블럭으로 변환
                        file_block = file.read(BLOCK_SIZE)

                        # 파일을 읽어 왔는데 비어 있을 때
                        if not file_block:
                            print("[END] 파일을 전부 보냈습니다.")
                            break

                        # 블럭 번호가 0 초과일 때 예상 블럭 코드를 1을 추가
                        if block_number > 0:
                            expected_block_number += 1

                        # 예상 블럭 코드와 파일 블럭을 보냄
                        send_DATA(expected_block_number, file_block, server_socket)
                    else:
                        print("[ERROR] 블럭 번호가 일치하지 않습니다!")

                # opcode가 ERROR일 때
                elif opcode == OPCODE['ERROR']:
                    # 받은 블럭에서 오류 코드를 추출
                    error_code = int.from_bytes(data[2:4], byteorder='big')

                    print(f"[ERROR] {ERROR_CODE[error_code]}")
                    break
                else:
                    break
            # 타임 아웃 예외 처리
            except socket.timeout as e:
                print("Timeout!! : 타임 아웃되어 다시 보냅니다.")

                # 타임 아웃 예외 처리가 됐을 때 예상 블럭 번호를 -1 함
                expected_block_number -= 1

                continue