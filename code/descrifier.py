import csv
import os
import math
import hashlib
from PIL import Image
import sys
from copy import copy
import random


# --------------- How to display an image---------------------
# bytesToImages(path,name=''), name set to '' if you don't know the name

# -------------- How compute the file description --------------------
# make_description(name,path) do a file name.desc

# -------- How to transform a file description into a dictionary -----
# dico = readDescrifier(file.desc) transform the file.desc into a dictionary

# ---------- How to have information from the disctionary ------------
# dico[id]['sha1pages'] // dico[id]['size']

# description['size Book']= str(sizeBook)                # size of the book
# description['adress']= str(adressRep)                  # adress of the book
# description['name']= str(nameFolder)                   # name of the book
# description['tracker']= str(tracker) #Not sure         # tracker
# description['Pages']=pieces                            # informations of chunks
# description['nb chunks']=len(description['Pages'])


def sizeFolder(path):
    # ---
    # This function compute the size of a folder
    # input  : path of the folder
    # output : size of the folder
    # ---
    size = 0
    for dirpath, dinames, filenames in os.walk(path):
        for i in filenames:
            f = os.path.join(dirpath, i)
            size += os.path.getsize(f)

    return size


def cut(folder, sizeP, idBook, name):
    # ---
    # This function cut our folder into chunk, we use this function into descrifier() function
    # Input  : the path of the folder, the size of our chunks and the id of the book
    # Output : a dictionary for the chunks
    # ---

    dictPage = dict()

    dir = os.listdir(folder)
    id = 0  # id for chunks

    for images in dir:
        with open(os.path.join(folder, images), "rb") as image:  # open images

            while True:
                descPages = dict()

                fileI = image.read(sizeP)  # read sizeP bytes of our image
                if not fileI:  # finish
                    break
                id += 1
                if(not os.path.exists('./bytes')):
                    os.makedirs('./bytes')
                if id < 10:
                    fileBook = open('./bytes/'+str(idBook) + '00' + str(id) + ".txt", "a+")
                elif id < 100 and id >= 10:
                    fileBook = open('./bytes/'+str(idBook) + '0' + str(id) + ".txt", "a+")

                fileBook.write(str(fileI))

                # id set +1 for the next chunks
                descPages['sha1pages'] = hashlib.sha1(str(fileI)).hexdigest()  # compute sha1
                descPages['size'] = len(str(fileI))  # compute size of the chunk
                if id < 10:
                    dictPage[str(idBook) + '00' + str(id)] = copy(descPages)
                elif id < 100 and id >= 10:
                    dictPage[str(idBook) + '0' + str(id)] = copy(descPages)

                    fileBook.close()

    return dictPage


def descrifier(nameFolder, adressRep, tracker=0):
    # ---
    # This function make dictionary for make the desciption file
    # Input : name and path of our repesitory, maybe the trackers
    # Output : information for the description file
    # ---

    global idBook
    idBook += 1  # When we have to do a descrifier we have to update the id of the book

    description = dict()
    sizeBook = sizeFolder(adressRep)  # sizeFolder(adressRep)

    sizePages = 256000  # max size of each chunk in B
    description['Pages'] = dict()  # Pages is a book with information about all chunks
    pieces = cut(adressRep, sizePages, idBook, nameFolder)  # dictionary of our chunks

    description['size Book'] = str(sizeBook)  # size of the book
    description['adress'] = str(adressRep)  # adress of the book
    description['name'] = str(nameFolder)  # name of the book
    description['tracker'] = str(tracker)  # Not sure         # tracker
    description['Pages'] = pieces  # informations of chunks
    description['nb chunks'] = len(description['Pages'])  # number of chunks

    return description


def read_dict(dictionnary, file):
    # ---
    # This function is used to read a dictionary and put on the file .desc
    # Input : a dictionary and the file
    # ---
    for cle, valeur in dictionnary.items():
        if type(valeur) is dict:

            file.write(cle + "\n")
            if (cle != 'Pages'):
                file.write("[\n")
            read_dict(valeur, file)
            file.write("]")
        else:
            file.write(cle + "\n" + str(valeur))
        file.write("\n")


def make_description(name, path):
    # ---
    # This function write the desciption file
    # Input : name and path of our repository
    # Output : the description file .desc
    # ---
    desc = descrifier(name, path)
    file = open(name + ".desc", "w")
    read_dict(desc, file)
    file.write("EOF")


def readDescrifier(path):
    # ---
    # This function take information from the description file and put it on dictionary
    # Input : name and path of our repository
    # Output : dec = readDescrifier("./test.desc")
    # ---
    description = dict()
    descPage = dict()
    desc_page = dict()
    with open(path, "r") as descr:
        info = descr.readline()
        while ((info != "EOF") and (len(info) > 0)):
            if (info == "Pages\n"):
                while (info[:-1] != ']' or info != ''):
                    info = descr.readline()
                    if (info[:-1] == ']'):
                        break
                    id = int(info[:-1])

                    info = descr.readline()
                    info = descr.readline()

                    if (info[:-1] == 'size'):
                        info = descr.readline()
                        descPage['size'] = int(info)
                        info = descr.readline()
                        if (info[:-1] == 'sha1pages'):
                            info = descr.readline()
                            descPage['sha1pages'] = bytes(info[:-1], 'utf-8')
                            info = descr.readline()
                    elif (info[:-1] == 'sha1pages'):
                        info = descr.readline()
                        descPage['sha1pages'] = bytes(info[:-1], 'utf-8')
                        info = descr.readline()
                        if (info[:-1] == 'size'):
                            info = descr.readline()
                            descPage['size'] = int(info)
                            info = descr.readline()
                    desc_page[int(id)] = copy(descPage)

            else:
                if (info[:-1] == "]"):
                    info = descr.readline()

                else:
                    id1 = info[:-1]
                    info = descr.readline()
                    description[id1] = info[:-1]
                    info = descr.readline()
            description['pages'] = desc_page
    # for cle,valeur in description.items():
    # print(cle,":",valeur)
    # print(description)
    return description


def bytesToImages(path, name=''):
    # ----
    # Compute the image for bytes
    # input : path
    # output : folder result this your image
    # ------

    fich = os.listdir(path)
    for temp in fich:
        with open(os.path.join(path, temp), 'r') as fileF:
            if len(name) == 0:
                path2 = './result/'
            else:
                path2 = './' + name + '/'
            if not os.path.exists(path2):
                os.makedirs(path2)
            with open(path2 + temp[:-3] + '.jpg', 'wb') as image:
                for f in fileF:
                    
                    image.write(bytes(f))


idBook = 9
if __name__ == '__main__':
    
    
    if len(sys.argv)==3:
        make_description(sys.argv[1],sys.argv[2])
    else:
        print("Missing argument pyhton descrifier.py [name] [path]")
    