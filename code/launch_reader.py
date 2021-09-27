from reader import *

# For Thibaud :
# cd Documents/M1\ MLDM/Networks/Projet/2021-net-a/code/
# python repository.py
# python reader.py test_/ True
# python reader.py test_2/ False
# python reader.py test_3/ False
# python reader.py test_4/ False
# python reader.py test_5/ False
# python reader.py test_6/ False
# python reader.py test_7/ False
# python reader.py test_8/ False
# python reader.py test_9/ False
# python reader.py test_10/ False





def main():
    if len(sys.argv) > 1:
        folders = []
        for i in (1, len(sys.argv)):
            folders.append(sys.argv[i])
        launch(folders)
    else:
        folders = ["test_/", "test_2/", "test_3/", "test_4/", "test_5/",
                  "test_6/", "test_7/", "test_8/", "test_9/", "test_10/"]
        launch(folders)


def launch(folders):
    silent = True
    for i in range(len(folders)):
        thread_launch_reader(folders[i], silent).start()
        time.sleep(0.5)
        silent = False


def thread_launch_reader(folder, silent):
    def handle():
        launch_reader(folder, silent)

    t = Thread(target=handle)
    return t


if __name__ == '__main__':
    main()
