#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 1                    shawak@dukes.jmu.edu             #
#                              September 27, 2015               #
# Simple File Server Implementation                             #
#                                                               #
# filename:  cloud_client.py                                    #
#                                                               #
# This program implements the client side of the file server.   #
# It issues  "commands" to the server.                          #
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
import os
import sys
import time

# define function to display a
# simple menu
def displayMenu():
    print('')
    print ('Menu')
    print ('----')
    print ('1) Upload a File')
    print ('2) Download a File')
    print ('3) Local Directory Listing')
    print ('9) Exit')
    return input()

# function to convert a number
# to bytes that can be directly
# sent over a socket
def convert_to_bytes(number):
    bytesvalue = bytearray()
    bytesvalue.append(number & 255)
    for i in range(3):
        number = number >> 8
        bytesvalue.append(number & 255)
    return bytesvalue

# function to convert a set of 4 bytes
# to an integer value
def bytes_to_number(bytesvalue):
    number = 0
    for i in range(4):
        number += bytesvalue[i] << (i*8)
    return number


# define variables
server_hostname = 'localhost'  # set host to localhost
port = 5077                    # set port to 5077

# determine local system type of encoding
encoding_type = sys.getfilesystemencoding()

try:
    # build the initial socket
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to the socket
    socket.connect((server_hostname, port))
except:
   print ('unable to connect to the server at:' + server_hostname + ':' + str(port))
   exit(2)

# display the menu until valid menu options are
# selected and the program is complete
while True:

    # display a menu
    menuOption = displayMenu()

    # allow the user to upload a file to the server
    if menuOption == '1':
        filename = input('File to upload: ')

        # validate that the file exists
        if os.path.exists(filename):

            # Tell the server that we are getting
            # ready to send the file
            command = 'sendtoserver'
            socket.sendall(command.encode(encoding_type))

            # allow the server time to process the command
            # NOTE:  This is not the best solution to handle
            #        message transfer over sockets. Working
            #        on setting up better message handling
            #        in next version.
            time.sleep(1)

            # now tell the server the name of
            # the file that the client is sending
            socket.sendall((filename).encode(encoding_type))

            # now send to the server the size of the file.
            filesize = os.path.getsize(filename)
            socket.sendall(convert_to_bytes(filesize))

            # open and send the entire file
            # to the client 
            with open(filename, 'rb') as file_to_send:

                # Grab first 1024 bytes of the file
                data = file_to_send.read(1024)

                # while there is still data to send
                while data:

                    # send the data
                    socket.send(data)

                    #grab more data and interate
                    data = file_to_send.read(1024)

            # We are finished sending the file.
            # Issue an alert to the console.
            print ('Finished sending file: ' + filename)

            # close the file.
            file_to_send.close()
        else:
            # the user picked a nonexistent file.
            print ('file ' + filename + ' does not exist! Check case and try again.')

    # handle the downloading of a file from the server
    elif menuOption == '2':

        # build the command to be sent to the server
        command = 'downloadfromserver'

        # and send the command
        socket.sendall(command.encode(encoding_type))

        # tell the server which file that
        # we want to download
        print ('File to download: ')
        filename = input()
        socket.sendall(filename.encode(encoding_type))

        filesize = socket.recv(4)                   # selecting 4 bytes means that the file cannot be over 1 GB
        filesize = bytes_to_number(filesize)        # convert the bytes to an integer value

        # if the file is 0 bytes in size, the user selected a file that did not exist.
        if (filesize == 0):

            # tell the user that the file does not exist
            print ('File does not exist!')
        else:
            # else we have a valid file and can proceed
            receivedAmount =  0

            # open a local file to store the new data
            with open(filename, 'wb') as file_to_write:

                # while there is more data to be received
                while receivedAmount < filesize:

                    # grab the data in 1024 byte chunks
                    data = socket.recv(1024)

                    # if no more data, we are done
                    if not data:
                        break

                    # determine if we've received all of the file contents
                    if len(data) + receivedAmount > filesize:

                        # add the new data to the buffer
                        data = data[:filesize-receivedAmount]

                    # increment our data received counter
                    receivedAmount += len(data)

                    # and we can write the data to the local file
                    file_to_write.write(data)

                # close the file
                file_to_write.close()

    # allow the user to see what local files
    # they have to work with
    elif menuOption == '3':
        # print the local files to the console
        print ('Client Directory Listing: ')

        # call a python function to enumerate the local files
        dirs  = os.listdir('.')

        # print out all of the local files in the currect directory
        for file in dirs:
            print (file)

    # allow the user to terminate processing
    elif menuOption == '9':
        print ('Shutting down client. ')

        # tell the server that we are shutting down
        # and tell the server to do the same
        command = 'shutdownserver'

        # send the command to the server
        socket.sendall(command.encode(encoding_type))

        # shutdown and close the socket
        socket.shutdown(1)
        socket.close()
        break
    else:
        # we recived an invalid menu option.  Tell
        # user and rebuild the menu.
        print ('Invalid input!  Try again.')