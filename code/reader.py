import os, sys, socket, time, queue
from copy import deepcopy
from threading import Thread
from hashlib import sha1
import numpy as np
from descrifier import *
from random import sample
from sys import argv
from math import inf


server_IP = 'localhost'
server_port = 9998
own_port = 12345
'''
# own_IP = None
list_reader = []
missed_pages = []
owned_pages = []
in_progress = dict()
dico_wanted = dict()
dico_page = dict()'''


# STATE 1 (INITIAL)
# TODO if we receive an uncomplete page we have to possibilities (either the problem occurs when
# the file is sent then we TODO should ask to an other peer to solve the pb or the pb come from a corrupted file (
# check the sha1)

def path_folder(path=None):
    ''' function which return a path, work, don't test it
    :param path:
    :return:
    '''
    if path == None:
        if sys.platform == 'linux' or 'linux1' or 'linux2' or 'darwin':
            path = os.getcwd() + '/'
        elif sys.platform == 'win32':
            path = os.getcwd() + '\\'
    return path


def initialisation_pages(desc, path):
    '''
    TO TEST
    this function return a list of owned pages in bytes, the list of owned page and a list of missed pages
    :param name: name of the book, type: str ex:'Marvel'
    :param path: path of the book
    :return: pieces_owned, pieces_missed : a list of the page we have and a list of a page we don't have type for both :
    [ID_page1, ...., ID_page_n] where ID_page_i is the ID of a page, a 5-digit number, ex : 10001
    '''
    list_own_pages = os.listdir(path)
    list_book_pages = list(desc['pages'].keys())
    pieces_owned = []
    pieces_missed = []
    #print(path)
    for page_ID in list_book_pages:
        if str(page_ID) + '.txt' in list_own_pages:
            page = load_page(page_ID, path)
            if sha1(page.encode('utf-8')).hexdigest() == desc['pages'][page_ID]['sha1pages'].decode('utf-8'):
                pieces_owned.append(page_ID)
            else:
                pieces_missed.append(page_ID)
        else:
            pieces_missed.append(page_ID)
    return pieces_owned, pieces_missed


# STATE 2 FONCTIONNE
def thread_list_readers(queue, missed_pages, silent):
    '''
    IF YOU CAN, TEST IT
    test if adress_IP is an adress_IP
    if list_reader is a list reader
    if dico_wanted is the dico wanted
    headbeat for list reader. Don't test it.
    '''

    def get_list():
        # print("Connection to the server")
        own_IP = connection_to_server()
        print("My IP address is :", own_IP)
        queue.put(('repository', own_IP))
        time.sleep(3)
        while True:
            # print("Request for the list of readers in progress of the reader :", address_IP)

            list_readers = get_list_readers(own_IP)  # uptade of the list_readers
            # print("List of readers update", list_readers)
            queue.put(('repository', list_readers))
            if not silent:
                dico_wanted = connection_other_readers(list_readers, own_IP, missed_pages)
                # print("Dictionary of List of pages for each reader update")
                queue.put(('repository', dico_wanted))
                time.sleep(60)

    t = Thread(target=get_list)
    return t


def connection_to_server():
    # test if adress_IP is an adress_IP
    global server_IP
    global server_port
    # ("create connection with server :", server_IP, server_port)
    s = socket.create_connection((server_IP, server_port))
    msg = 'CON'
    s.sendall(msg.encode('utf-8'))  # Ask a part of the list

    size_IP = 11
    res = s.recv(size_IP)
    s.settimeout(10)
    adress_IP = res.decode("utf-8")
    s.close()
    return adress_IP


def get_list_readers(own_IP):
    '''
    ask the list of the reader to the repository part
    :return: list of reader, where a reader is defined by his port ex [reader1, ... readern] where reader1 = 1234
    '''
    global server_port
    global server_IP

    # print('get list reader, create connection :', server_IP, server_port, own_IP)

    s = socket.create_connection((server_IP, server_port), source_address=(own_IP, own_port))
    s.settimeout(10)

    msg = str('LST')
    list_readers = []
    size_line = 11
    s.sendall(msg.encode('utf-8'))
    while True:
        try:
            res = s.recv(size_line).decode("utf-8")
            if len(res) > 1:
                list_readers += [res]
                s.settimeout(1)
            elif len(res) == 0:
                break
        except socket.timeout:
            break
    s.close()
    # print("get_list_readers", list_readers)
    return list_readers


# --------------------- STATE 3 ---------------------------------

def connection_other_readers(list_readers, own_IP, missed_pages):
    '''
    test if the outpu is tab_wanted :
    dict_wanted = {reader_IP_1 : list_page_wanted, ..., reader_IP_n : list_page_wanted]
    list_page_wanted : list of page that the other reader have and we don't have.
    :param list_readers:
    :param own_IP:
    :param missed_pages:
    :return:
    '''

    storage_wanted_list = queue.Queue()
    list_thread = []
    for reader_port in list_readers:
        t = thread_other_reader(reader_port, own_IP, missed_pages, storage_wanted_list)
        list_thread.append(t)
        t.start()

    for t in list_thread:
        t.join()
    tab_wanted = creation_dico_wanted(storage_wanted_list, list_readers)
    return tab_wanted


def thread_other_reader(reader_IP, own_IP, missed_pages, storage_wanted_list):
    '''
    return for reader i the list of page its has and we don't have
    :param reader_IP:
    :param reader_port:
    :param storage_wanted_list: queue
    '''
    global server_port
    def get_connection():
        # TODO ajouter securite si liste reader vide
        # print("get_connection", reader_IP, own_IP)
        s = socket.create_connection((reader_IP, server_port)) #, source_address=(str(own_IP), 12345))
        available_pages = ask_list(s, reader_IP)  # list
        s.close()
        wanted_list = compare_list(available_pages, missed_pages)
        storage_wanted_list.put((reader_IP, wanted_list))
    t = Thread(target=get_connection)
    return t


def ask_list(s, reader_IP):
    '''
    function who send a message to ask the page to an other reader and receive the list of available page of the other readers
    :param s: type : socket
    :return: list of page of the other reader
    '''
    msg = 'ASK'  # message to ask the list of reader
    s.sendall(msg.encode('utf-8'))
    available_pages = []
    while True:
        try:
            res = s.recv(5).decode("utf-8")
            # print(res)
            if not res:
                break
        except socket.timeout:
            send_error_server(reader_IP)
            break
        available_pages.append(int(res))
    return available_pages


def creation_dico_wanted(storage_wanted_list, reader_list):
    '''
    Don't test
    a dico with for each reader a list of the pages that it have and we want type : dico. ex : {reader_1: list_wanted,
    ... , reader_n: list_wanted}
    Be carefull
    :param storage_wanted_list: a queue where each element of the queue is of type : (reader, list_of_wanted_pages) type
    : QUEUE ! ex : queue((reader1, list_wanted1), ..., (reader1, list_wanted1))
    :param reader_ID: list of reader where each reader is define by his port (be careful, reader_list is not equal all
    the time to the global variable port_list
    :return:
    '''
    dico_wanted = dict()
    for i in range(len(reader_list)):
        reader, wanted = storage_wanted_list.get()
        dico_wanted[reader] = wanted
    return dico_wanted


def send_error_server(reader_IP):
    'Send a message to the repository when you can t connect to an other reader'
    s = socket.create_connection(('localhost', server_port))
    msg = 'ERR'
    s.sendall(msg.encode("utf-8"))
    msg = reader_IP
    s.sendall(msg.encode("utf-8"))
    s.recv(3)
    s.close()
    return


# ----------------------STATE 4----------------------------


def compare_list(available_pages, missed_pages):
    """ compare the list of available pages of an reader with our own list and return
    the list of pages that we need. Dont test
    :param available_pages:
    :param missed_pages:
    :return:
    """
    wanted_list = []
    for missing in missed_pages:
        for available in available_pages:
            if missing == available:
                wanted_list.append(missing)
    return wanted_list


def pages_with_no_know_peer(new_missed, tab_pages):
    '''
    create a list of page where there is no reader who have this page
    :param tab_pages:
    :return:
    '''
    tab = np.copy(tab_pages)
    list_pages_unknown = []
    try:
        while np.min(np.sum(tab, axis=0)) == 0:
            rare_page = np.argmin(np.sum(tab, axis=0))
            list_pages_unknown.append(new_missed[rare_page])
            tab[:, rare_page] = inf
    except ValueError:
        pass
    return list_pages_unknown, tab


def priority2(available_reader, dico_wanted, old_missed_pages, in_progress):
    temp_missed_pages = deepcopy(old_missed_pages)
    for page in in_progress.values():
        if page in temp_missed_pages:
            temp_missed_pages.remove(page)

    if temp_missed_pages == []:
        return None, in_progress

    for page in dico_wanted[available_reader]:
        if page in temp_missed_pages:
            in_progress[available_reader] = page
            return page, in_progress

    in_progress[available_reader] = temp_missed_pages[0]
    return temp_missed_pages[0], in_progress

def priority(available_reader, dico_wanted, missed_pages, in_progress):
    '''
    test if the output is a page we need and this page is not in owned_pages xor in_progress
    maybe not the first function to test
    this function manages the priorities for requesting a page, that is, which page should be requested from a reader?
    :param available_reader: the reader to whom we want to request a page. type : port_reader, a number. ex : 12345
    :param dico_wanted: a dico with for each reader a list of the pages that it have and we want type : dico. ex : {reader_1: list_wanted, ... , reader_n: list_wanted}
    :param missed_pages: list of pages that we want
    :param in_progress: dico with for each reader, the page that it currently search
    :param waiting_answer_list: list of priorited pages because asked by the server part of reader ex: [ID_page1, ID_page2, ..., ID_page_N]
    :return: the wanted page, type : ID_page, a a 5-digit number
    '''

    # Created a tab_pages, with for each line a reader, and each colomn a missed page
    new_missed = missed_pages  # page missed taking into account the page currently asked
    for page in in_progress.values():
        if page in new_missed:
            new_missed.remove(page)
    new_wanted = dict()  # dico with for each reader the wanted page (missed page not distributed that the reader have)
    for reader in dico_wanted.keys():
        new_wanted[reader] = compare_list(dico_wanted[reader], new_missed)
    tab_pages, list_reader = convert_table_priority(new_wanted,
                                                    new_missed)  # tab of reader / pages, list of reader associed
    #print("306", missed_pages, new_missed)
    #print("309", tab_pages)
    unknowned_pages, tab = pages_with_no_know_peer(new_missed,
        tab_pages)  # Pages that no readers has, tab without the pages that no reader have
    #print("307", tab)
    # Manage the priority of the waiting_answer_list
    #print("327", dico_wanted[available_reader])
    # Manage the priority by order of rarity
    for i in range(len(dico_wanted[available_reader])):  # search a page that he have by order of rarity
        index_of_available_reader = list_reader.index(available_reader)
        rarest_page = np.argmin(np.sum(tab, axis=0))

        if tab[index_of_available_reader, rarest_page] == 1:
            in_progress[available_reader] = new_missed[rarest_page]
            return new_missed[rarest_page], in_progress
        else:
            tab[:, rarest_page] = 0

    # Else, it will ask a unknowed page
    in_progress[available_reader] = unknowned_pages[0]
    #print("332", unknowned_pages[0], in_progress)
    return unknowned_pages[0], in_progress


def convert_table_priority(dico_wanted, missed_pages):
    '''Convert dico wanted and missed page to create a numpy of pages'''
    tab = np.zeros((len(dico_wanted.keys()), len(missed_pages)))  # nb de reader * nb missed pages
    i = 0
    list_reader = []
    for reader in (dico_wanted.keys()):
        list_reader += [reader]
        wanted_pages_per_reader = dico_wanted[reader]  # liste des pages qu'ils ont
        for j in range(len(missed_pages)):
            for missed in wanted_pages_per_reader:
                if missed == missed_pages[j]:
                    tab[i, j] = 1
        i += 1
    return tab, list_reader


def thread_ask_page(reader_IP, page_ID, q, desc):
    """Thread who ask page, don't test"""
    def get_page():
        # TODO if timeout send_error_server(reader_port)
        s = socket.create_connection((reader_IP, server_port))
        s.settimeout(10)
        page = ask_page(s, page_ID, reader_IP, desc)  # page if page = None soucis avec sha1 ou pas recue
        s.close()
        q.put(('reader', (page_ID, reader_IP, page)))

    t = Thread(target=get_page)
    return t


def ask_page(s, page_ID, reader_IP, desc):
    ''' function which ask a page to an other reader
    maybe, check if the other reader receive the msg 'PAG' and send the a page, if page is empty, it's an error.'''
    #print("ask page nb", page_ID, "to", reader_IP)
    msg = 'PAG'  # message to ask the list of reader
    s.sendall(msg.encode('utf-8'))
    msg = page_ID  # message to ask the list of reader
    s.sendall(str(msg).encode('utf-8'))
    print("Ask for page", page_ID, "to peer", reader_IP)
    page = ""
    try:
        flag = s.recv(3).decode("utf-8")
        if flag == 'SEN':
            size_page = desc['pages'][int(page_ID)]['size']
            page = s.recv(size_page).decode("utf-8")  # TODO check if page se decode bien
        else:
            s.settimeout(20)                # TODO check if page se decode bien
    except socket.timeout:
        send_error_server(reader_IP)
        return None
    if len(page) > 1:
        if sha1(page.encode("utf-8")).hexdigest() == desc['pages'][page_ID]['sha1pages'].decode('utf-8'):
            return page
    return None


def thread_server_behavior(q, q_server, path, desc, owned_pages):
    def handle(owned_pages):
        dico_wanted = None
        answer, own_IP = q_server.get()
        server_socket = socket.socket()
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((own_IP, server_port))  # 0.0.0.0 listen on all interfaces #
        server_socket.listen()
        #print("409",owned_pages)
        while True:
            try:
               # print("413")
                answer, element = q_server.get(block=False)  # update of the variable
                owned_pages, in_progress, dico_wanted = element
                pass
            except queue.Empty:
                pass
            # accept new clients connections,
            # and start a handle_client thread every time
            sock_request, addr = server_socket.accept()  # !!! BLOCKING
            # print("ACCEPTED", addr)
            #print("423")
            handle_server(sock_request, path, owned_pages, dico_wanted, desc, own_IP, addr[0], q).start() # start a thread when a new client is connected
    t = Thread(target=handle, kwargs={'owned_pages': owned_pages})
    return t


def handle_server(socket, path, owned_pages, dico_wanted, desc, own_IP, other_reader_IP, q):
    size = 5  # max nb of caracters that can be received
    '''test if for each message, we answer the good answer (the if works)'''
    def handle():
        #print("432")
        request_code = socket.recv(3).decode("utf-8")
        #if request_code != 'HBT' and request_code != 'ASK':
        #('Message received : ', request_code)
        if request_code == 'HBT':
            output = 'ALV'
            socket.sendall(output.encode('utf-8'))
        elif request_code == 'ASK':
            for i in range(len(owned_pages)):
                output = str(owned_pages[i])
                socket.sendall(output.encode('utf-8'))

        elif request_code == 'PAG':
            page_ID = int(socket.recv(5).decode('utf-8'))
           # print("Peer", other_reader_IP, "ask for page", page_ID, "to peer", own_IP)
            #print(owned_pages)
            if page_ID in owned_pages:  # add int to transform str in int

                output = 'SEN'
                socket.sendall(output.encode('utf-8'))
                page = load_page(page_ID, path)
                socket.sendall(page.encode('utf-8'))
                # print('Page sent \n')
            else:
                if dico_wanted :
                    # print('Wait, we ask the page to an other reader\n')
                    reader = search_reader(page_ID, dico_wanted)
                    output = 'ATT'
                    socket.sendall(output.encode('utf-8'))
                    t_ask_page = thread_ask_page(reader, page_ID, q, desc)  #fonctionne only if scilient reader have all pages
                    t_ask_page.start()
                    t_ask_page.join()
                    page = load_page(page_ID, path)
                    socket.sendall(page)
                   # print('Page sent \n')
                    # we don't need to send a message if timeout bc if this peer has a timeout error
                    # the requesting peer already had one

    t = Thread(target=handle)
    return t


def search_reader(page_ID, dico_wanted):
    '''don't test it'''
    for reader in dico_wanted.keys:
        if page_ID in dico_wanted[reader]:
            return reader
    else:
        return sample(dico_wanted.keys, 1)


def thread_reader_behavior(q, q_reader, desc, path):

    def handle():
        element = q_reader.get()  # TODO send message in manage queue
        dico_wanted, missed_pages, in_progress = element
        #print("reader behavior", dico_wanted, missed_pages)
        for reader_IP in list(dico_wanted.keys()):
            # page_ID, in_progress = priority(reader_IP, dico_wanted, missed_pages, in_progress)
            # thread_ask_page(reader_IP, page_ID, q, desc).start()
            page_ID, in_progress = priority2(reader_IP, dico_wanted, missed_pages, in_progress)
            q.put(('pages', in_progress))
            if page_ID:
                thread_ask_page(reader_IP, page_ID, q, desc).start()
        while True:
            #print("481", dico_wanted, missed_pages, in_progress)
            #time.sleep()
            if book_is_complete(desc, path):
                break
            try:
                element = q_reader.get()  # update of the variable
                dico_wanted, missed_pages, in_progress = element
            except queue.Empty:
                pass
            #print("507", missed_pages, list(in_progress.values()))
            if len(list(in_progress.keys())) < len(list(dico_wanted.keys())):
                for reader_IP in list(dico_wanted.keys()):
                    if reader_IP not in list(in_progress.keys()):
                        #print("484", missed_pages, in_progress)
                        if missed_pages != list(in_progress.values()):
                            page_ID, in_progress = priority2(reader_IP, dico_wanted, missed_pages, in_progress)
                            q.put(('pages', in_progress))
                            if page_ID:
                                thread_ask_page(reader_IP, page_ID, q, desc).start()
                            '''page_ID, in_progress = priority(reader_IP, dico_wanted, missed_pages, in_progress)
                            q.put(('pages', in_progress))
                            thread_ask_page(reader_IP, page_ID, q, desc).start()'''
    t = Thread(target=handle)
    return t

def thread_manage_queue(q, q_server, q_reader, path, owned_pages, missed_pages):
    '''thread which manage all information between reader
    if you can, test all the possibilites
    normally it's work'''
    def get_queue():
        in_progress = dict()
        dico_wanted = dict()
        while True:
            origin, element = q.get()
            # print("thread_manage_queue", element)
            if origin == 'repository':
                if type(element) == str:
                    own_IP = element
                    q_server.put(("own_ip", own_IP))
                elif type(element) == list:
                    list_readers = element
                else:
                    dico_wanted = element

            if origin == 'pages':
                in_progress = element

            if origin == 'reader':
                page_ID, reader_IP, page = element  # TODO change reader port
                page_ID = int(page_ID)
                if page:
                    #print(562, len(page))
                    if page_ID in missed_pages:
                        missed_pages.remove(page_ID)
                    owned_pages.append(page_ID)
                    #print("565",in_progress)
                    #print("566",page_ID, type(page_ID))
                    del in_progress[reader_IP]
                    download_page(page, page_ID, path)
                else:
                    if reader_IP in dico_wanted[reader_IP]:
                        dico_wanted[reader_IP].remove(page_ID)
                    del in_progress[reader_IP]

            q_server.put(("updt", (owned_pages, in_progress, dico_wanted)))
            if dico_wanted != {}:
                q_reader.put((dico_wanted, missed_pages, in_progress))

    t = Thread(target=get_queue)
    return t


def load_page(page_ID, path):
    '''
    load the page on our folder. Work
    :param page_ID:
    :return:
    '''
    file = open(path + str(page_ID) + '.txt', 'r')
    return file.read()


def download_page(page, page_ID, path):
    """download a page on our folder"""
    file = open(path + str(page_ID) + '.txt', 'w')
    file.write(str(page))


def book_is_complete(desc, path):
    #print("Is book complete ?", len(os.listdir(path)), len(list(desc['pages'].keys()))+1)
    if len(os.listdir(path)) == len(list(desc['pages'].keys()))+1:
        print("I'm done !")
        return True
    return False


def deregister(own_IP):
    '''check if wen we call this function, the reader is deregristed on the repository'''
    s1 = socket.create_connection(('localhost', server_port), source_address=(own_IP, 0))
    s1.sendall(str('DRG').encode('utf-8'))
    answer = s1.recv(3).decode("utf-8")
    if answer != 'DNE':
        deregister(own_IP)
    else:
        sys.exit()


def launch_reader(name_folder, silent=False):
    '''
    :param name_folder:
    :param silent:
    :return:
    '''
    sys.tracebacklimit = 0
    own_IP = None    # INITIALISATION

    # State 1 INITIALISATION
    # path = path_folder('..')
    path = '../Page_Folder/' + name_folder
    name_desc = 'Test_.desc'

    desc = readDescrifier(path + name_desc)
    owned_pages, missed_pages = initialisation_pages(desc, path)
    # print('owned pages', owned_pages)
    # print('missed pages', missed_pages)

    q = queue.Queue()
    q_server = queue.Queue()
    q_reader = queue.Queue()

    # STATE 2
    # Thread_start
    thread_manage_queue(q, q_server, q_reader, path, owned_pages, missed_pages).start()  # TODO voir si dico_page c'est sa place

    # State 2

    thread_list_readers(q, missed_pages, silent=silent).start()
    # print("Start of the thread server behavior, our IP is ", own_IP)
    thread_server_behavior(q, q_server, path, desc, owned_pages).start()

    if not silent:
        thread_reader_behavior(q, q_reader, desc, path).start()
    while True:
        prompt = input('>')
        if prompt == "end":
            deregister(own_IP)

if __name__ == '__main__':
    if argv[2] == "True":
        launch_reader(argv[1], True)
    else:
        # ("False")
        launch_reader(argv[1], False)