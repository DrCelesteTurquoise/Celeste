import socket

HOST = '192.168.12.250'
PORT = 50000
pose = '(-0.3,-0.5,0.3,0,-3.14,0)'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, address = s.accept()
    with conn:
        print('Connected by', address)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            if 'get pose' in str(data):
                conn.sendall(pose.encode())
                print('Data sent.')