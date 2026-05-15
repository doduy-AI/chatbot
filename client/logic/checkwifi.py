import socket

def is_connected(host="8.8.8.8", port=53, timeout=1):
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET , socket.SOCK_STREAM) as s : 
            s.connect((host, port))
        return "True"
    except(socket.timeout , OSError):
        return "False"
