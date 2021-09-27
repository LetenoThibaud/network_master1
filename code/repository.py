import queue
from threading import Thread
from time import sleep
import socket
from random import sample

repository_ip = 'localhost'
repository_port = 9998
BUFFER_SIZE = 1024
peer_list = []  # ['127.0.0.4', '127.0.0.5', '127.0.0.6', '127.0.0.7']
heartbeat_frequency = 30  # in seconds
count_ip = 2


def main():
    q = queue.Queue()
    handle_accept_connection(q).start()
    while True:
        print(peer_list)
        if peer_list:
            for ip in peer_list:
                # print("before hbt", ip)
                heartbeat_thread(ip).start()
        sleep(heartbeat_frequency)


def heartbeat_thread(ip):
    def handle():
        sock = socket.create_connection((ip, 9998))
        sock.settimeout(3)
        msg = 'HBT'
        try:
            sock.sendall(msg.encode('utf-8'))
            request_code = sock.recv(3).decode("utf-8")
            # print(request_code, ip)
            if request_code != 'ALV':
                print(request_code, '!=ALV', ip)
                peer_list.remove(ip)
        except socket.timeout:
            print("timeout", ip)
            peer_list.remove(ip)
    t = Thread(target=handle)
    return t


def get_list_to_send(peer_ip, sample_size):
    while True:
        to_return = sample(peer_list, sample_size)
        if peer_ip not in to_return:
            break
    return to_return


def send_list(sock, peer_ip):
    global peer_list
    min_size_list_to_send = 5
    #print("send list", peer_ip)
    if len(peer_list) <= min_size_list_to_send:
        for ip in peer_list:
            if ip != peer_ip:
                msg = str(ip)
                sock.sendall(msg.encode('utf-8'))
                sleep(0.3)
    elif len(peer_list) > min_size_list_to_send:
        list_to_send = get_list_to_send(peer_ip, min_size_list_to_send)
        for ip in list_to_send:
            msg = str(ip)
            sock.sendall(msg.encode('utf-8'))
            sleep(0.3)


def handle_accept_connection(q):
    def handle():
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', repository_port))
        server_socket.listen()

        while True:
            sock, addr = server_socket.accept()
            handle_request(sock, addr[0], q).start()

    t = Thread(target=handle)
    return t


# Flag list:
# CON : connect    (Peer sends request to repository and repository answers)
# DRG : deregister (Peer sends request to repository and repository answers)
# ERR : error      (Peer sends request to repository and repository answers)
# LST : list       (Peer sends request to repository and repository answers)
# HBT : heartbeat  (respository sends request to the peer and the peer answers)
def handle_request(sock, peer_ip, q):
    def handle():
        global count_ip
        global peer_list
        flag = sock.recv(3).decode("utf-8")
        if flag == 'CON':
            adress = "127.0.0." + str(count_ip)
            peer_list.append(adress)
            sock.sendall(adress.encode('utf-8'))
            count_ip += 1
        elif flag == 'LST':
            send_list(sock, peer_ip)
        elif flag == 'DRG':
            print(peer_list, peer_ip)
            peer_list.remove(peer_ip)
            msg = 'DNE'
            sock.sendall(msg.encode('utf-8'))
        elif flag == 'ERR':
            #  if receive error then there is another message
            #  with the number of the port that is not working
            #  we do heartbeat message just for this port to know if we remove it from the list
            problematic_ip = sock.recv(11).decode("utf-8")
            sock.sendall("RCV")
            heartbeat_thread(problematic_ip).start()
        sock.close()
    t = Thread(target=handle)
    return t


if __name__ == "__main__":
    main()