# School-NetworkProgramming-2023-1-FinalProject

# TFTP 클라이언트

## 소개
이 프로그램은 Python으로 작성된 간단한 TFTP (Trivial File Transfer Protocol) 클라이언트입니다.

## 기능
- 읽기 (RRQ) 및 쓰기 (WRQ) 작업을 모두 지원
- 다양한 TFTP 오류 코드에 대한 오류 처리를 구현
- 통신을 위해 UDP 소켓을 사용
- 사용자가 서버 IP 주소, 포트, 작업 유형 (get/put) 및 파일 이름을 지정 가능
- 기본 전송 모드는 `octet`

## 사용 방법
### 전제 조건
- Python 3.x

### 클라이언트 실행
1. 저장소를 복제하거나 `TFTP_Client.py` 파일을 다운로드합니다.
2. 터미널 창을 엽니다.

#### 명령어 구문
```bash
python TFTP_Client.py <server_ip> <operation_type> <filename> [-p PORT]
```

#### 인수
- `server_ip`: TFTP 서버 IP 주소
- `operation_type`: `get` (서버에서 파일 다운로드) 또는 `put` (파일을 서버에 업로드) 중 하나를 지정
- `filename`: 전송 파일 이름
- `-p (PORT)`: (선택 사항) TFTP 서버 PORT 번호, 기본 포트는 69입니다. (선택 사항)

### 예시

#### 파일 다운로드
```bash
python TFTP_Client.py localhost get example.txt
```

#### 파일 업로드
```bash
python TFTP_Client.py localhost put example.txt
```

## OCCODE
- 1: RRQ
- 2: WRQ
- 3: DATA
- 4: ACK
- 5: ERROR

## 오류 코드
TFTP 클라이언트는 다음과 같은 오류 코드를 처리합니다:
- 0: 정의되지 않은 오류
- 1: 파일을 찾을 수 없음
- 2: 액세스 위반
- 3: 디스크가 꽉 찼거나 할당이 초과됨
- 4: 잘못된 TFTP 작업
- 5: 알 수 없는 전송 ID
- 6: 파일이 이미 존재함
- 7: 해당 사용자가 없음