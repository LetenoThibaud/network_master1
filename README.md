# README
### 2021 Networking MLDM Team-A
####  BANASZEK/DEFOUR/LETENO/ROBIN

>Welcome to our meme sharing project! What would our world be without memes? Do you have enough memes? You never have enough memes! So we created a platform that enables peers to share large meme libraries with each other. The goal is to log on, select which library you want, and download quickly and efficiently across multiple peers to increase your meme inventory.

## FUNCTIONALITY
Build
--
- **The final code is temporary in the branch "final_code"**
- Download the project from [GitHub](https://github.com/UJM-INFO/2021-net-a)
- Create a folder for each reader to stock the image libraries to receive and send
- Dependencies
  - os, sys, numpy, random, socket, time, queue, copy, threading, hashlib
- Python Version 3 or above

Run
--
- Make sure you are in the "Code" working directory.
- Run the descrifier, it creates a desc file in the book (the folder with all the images).
```sh
python descrifier.py --"path of the readers where images are stored"
```
- Run repository, it starts the server.
```sh
python repository.py 
```
- First option for starting each reader (from reader folders created). Starts a each reader in a new thread. Make sure you write the list of the path for each reader in the code. 
  - Note, the first reader will be silent (this is a functionality not a bug :) )
```sh
python launch_reader.py test_/ test_2/
```
- Another option for starting the reader
  - Here you can put the reader paths directly into the terminal
```sh
python reader.py test_2/ False
```
- A test example is available:
```sh
python launch_reader.py 
```

Test
-- 
- We used this [helpful link](https://coderefinery.github.io/testing/gh-actions/) to set ourselves up with automated testing.
- Set up a few units tests to make sure messages were being sent and received properly.


## ARCHITECTURE

### Descrifier
| Descrifier | A file with the description of books to exchange|
| ------ | ------ |
| Book | A large file containing many meme images|
| Page | A chunk of a book and the exchange unit between readers|
| SHA1 | An error check to test integrity of file chunk |
|  | |

The descrifier begins by opening a book and iterating through the images determining image size. It breaks down images into 256000 B per page and each page is assigned an id within the book. This allows peers to exchange pages, identify which pages are most rare, and identify which pages are missing. The descrifier contains the address for the repository. It also contains a SHA1 check which is an identifiant for the pages. 

-----
-----
### Repository
| Repository | Maintains the list of all Readers on the Exchange Network|
| ------ | ------ |
| Reader | A client who connects to exchange books|
| Peer List | List of readers connected |
| Sublist | A random subset of Peers from Peer List |
| Heartbeat | A health check to determine the connectivity of a Reader |
| Flag List | List of all commands that can be exchanged between Readers and Repository |

- The repository is the first launched process, it houses and manages the Reader List of all the connected readers and check if the readers are in life. 

- The readers connect first to the repository which registers it and returns his Reader's IP adress and the list of the Reader's IP adress. This IP adress is added to the Peer List and is constantly updated as soon as a reader register or deregister. 

The Repository manages the network by:
- Allowing any reader to frequently ask for the Readers List to know the adrress of readers it can communicate with. For less than 5 Readers on the network, the Repository sends the entire Reader List on request. For more than 5 readers on the Readers List, a partial list is sent in order to create a true Peer-to-Peer network.
- Running a Heartbeat as a health check. At a predefinite frequency, the repository sends a message to all peers in the Readrs List and waits for an answer. 
   - If a reader does not respond in a given time window, the Reader is removed from the list. This ensures the removal of readers who may have crashed or are no longer on the network, in the case a Reader does not deregister themself.
   - It also has an error listener where any reader who tried to contact another reader and did not receive an answer in a given time window will send an error flag to the Repository containing the IP adrress of the problematic reader. After reception of the error the repository send a heartbeat to this specific reader. The Reader is deregistered if an error is received.

-----
-----
### Reader

| Reader | A peer who connects to the Repository with the intention of exchanging Books|
| ------ | ------ |
| Reader_launch | Initializes Readers|
| List_reader | Initializes Reader threads |
| Server_behavior | Messaging thread |
| Reader_behavior | Manages requests to the Reader | 
| Manage_queue | Receives pages and checks for errors |

See Reader Diagram reader_diagram[PB].png
-- 
- Runs function reader_launch 
  - Starts the different parts of the reader
  - Initializes queues and some variables
  - Starts a thread manage_queue which manages the infromation received by all the other threads and sends the necessary information to the other threads.

- Starts a thread list_reader 
  - Requests and receives the list of readers from the repository 
  - Asks each reader for their list of owned pages
  - Sends file deco_wanted which is a dictionary of {keys readers values pages} to manage queue
  - Rinse and repeat

- Starts a thread server_behavior
  - Sends and receives messages to and from the repository
  - Receives request for a list of pages, updates the list of owned pages, sends pages, and sends the important information to the requesting Reader

- Starts a thread reader_behavior 
  - Manages requests for the others readers, which page to ask which reader
  - Only asks one page at a time to a unique reader, to avoid traffic jams
  - Asks pages from different readers in parallel using threads

- Function manage_queue
  - The page is sent here when it is received
  - Checks the SHA1 and downloads the page if there are no errors

- The thread finishes when the book is complete, but the program remains in server mode
- To close the program, the reader is asked to write the word "end" in the console



















