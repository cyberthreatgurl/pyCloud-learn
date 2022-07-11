#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 1                    shawak@dukes.jmu.edu             #
#                              September 27, 2015               #
# Simple File Server Implementation                             #
#                                                               #
# filename:  cloud_server.py                                    #
#                                                               #
# This program implements the server side of the file server.   #
# It responds to "commands" issued from one single client.      #
# The current implementation does not allow for multithreaded   #
# communications among different clients.  The server responds  #
# to file download, upload and shutdown commands.               #
# User and session authentication is NOT performed.             #
# Requires:   Python3                                           #
# Tested on:  Windows 10, Ubuntu 14.04.3 LTS                    #
#                                                               #
# Version:  1.0        AKS       September 26, 2015             #
#                                                               #
#                                                               #
#################################################################
import socket
import sys
import os

#
def convert_to_bytes(number):
    bytesvalue = bytearray()
    bytesvalue.append(number & 255)
    for i in range(3):
        number = number >> 8
        bytesvalue.append(number & 255)
    return bytesvalue

def bytes_to_number(bytesvalue):
    number = 0
    for i in range(4):
        number += bytesvalue[i] << (i*8)
    return number

encoding_type = sys.getfilesystemencoding()

# Set the port number
server_port = 5077

# limit the number of connections to 1
max_server_connections = 1

# define the hostname of the server
host = 'localhost'

# create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# bind the socket to the IP address and port
server_address =  (host, server_port)
print ('starting up on %s port %s' % server_address)

try:
    sock.bind(server_address)
except socket.error as e:
    print(str(e))

# tell to the socket to listen for connections
sock.listen(max_server_connections)

print ('waiting for a connection...')

# tell the socket to accept any connections
(client, (client_address, client_port)) = sock.accept()

# print an alert to the console to indicate a user has connected
print ('Connection from:' + client_address + ":" + str(client_port))

# set up a loop to keep processing input
while True:

    # wait for a command from the client
    command = client.recv(32).decode(encoding_type)

    # if the client is getting ready to send a file
    # to the server
    if command == 'sendtoserver':
        filename = client.recv(128).decode(encoding_type)

        # Determine the size of the file that we are
        # getting ready to receive

        filesize = client.recv(4)         # selecting 4 bytes  means that the file cannot be over 1 GB in size
        filesize = bytes_to_number(filesize)   # unpack the bytes to determine actual integer value

        # set up a loop to keep receiving data while
        # there is more left in the file to receive
        receivedAmount =  0

        #open the local file for write
        with open(filename, 'wb') as file_to_write:
            # while the entire file has not been received
            while receivedAmount < filesize:
                #grab 1024 bytes at a time
                data = client.recv(1024)
                if not data:
                    break
                # If don't have the complete file yet, keep
                # receiving date
                if len(data) + receivedAmount > filesize:
                    # keep totalling the amount of data that has been received
                    data = data[:filesize-receivedAmount]

                # total up the amount of data received so far
                receivedAmount += len(data)

                # write the data to the local file
                file_to_write.write(data)

            # and close the file when complete
            file_to_write.close()

    # if the client would like to download a file
    elif command == 'downloadfromserver':

        # we should receive the filename right
        # after the command is received
        filename = client.recv(1024).decode(encoding_type)

        # check to see if we received a valid filename
        # and if it even exists
        if (os.path.exists(filename)):
            print ('Preparing to send:' + filename)
        
            # now send to the client the size of the file.
            filesize = os.path.getsize(filename)
            client.sendall(convert_to_bytes(filesize))

            # open and send the entire file
            # to the client 
            with open(filename, 'rb') as file_to_send:
                data = file_to_send.read(1024)
                while data:
                   client.send(data)
                   data = file_to_send.read(1024)
            print ('Finished sending file: ' + filename)
            file_to_send.close()
        else:
            # File does not exist, so let's send the client
            # a filesize of zero, so it can alert the user
            filesize = 0
            client.sendall(convert_to_bytes(filesize))
    # we have been told to shut down the server
    elif command == 'shutdownserver':

        # close the socket
        sock.close()
        break
    # handle weird or unexpected input
    else:
        print ('not sure what I received')
        print ('shutting down')

        # clean up and exit
        sock.close()
        exit(1)