#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 2                   shawak@dukes.jmu.edu              #
#                              October 25, 2015                 #
# Simple File Server Implementation                             #
#                                                               #
# filename:  cloud_client.py                                    #
#                                                               #
# This program implements the client side of the file server.   #
# It issues "commands" to the cloud server.                     #
# The cloud client is implemented as a basic menu-driven        #
# interface.  The user MUST enter a valid username and          #
# password.  This information is sent to the server inside      #
# a TLSv1.2 session for authentication.                         #
#                                                               #
# Requires:   Python3                                           #
# Tested on:  Windows 10, Ubuntu 14.04.3 LTS                    #
#                                                               #
# Version:  2.0        AKS       October 25, 2015               #
#               - Support added for multithreads and user       #
#                 authentication.  Also, a simple TLSv1.2       #
#                 session encryption has been added.            #
#                                                               #
#           1.0        AKS       September 26, 2015             #
#               - Basic implementation of a cloud server        #
#                                                               #
#                                                               #
#################################################################
import socket
import os
import sys
import time
import ssl
import hashlib
                       
# define function to display a
# simple menu
def displayMenu():
    print('')
    print ('Menu')
    print ('----')
    print ('0) Login')
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
s_hostname = 'localhost'          # set host to localhost
port = 5077                       # set port to 5077
cafile = "ca.crt"                 # use a self-signed certificate
protocol = ssl.PROTOCOL_TLSv1_2   # Set the Protocol to TLSv1.2
authenticated = False             # user authenticated flag

# determine local system type of encoding
encoding_type = sys.getfilesystemencoding()


# Build the SSL Connection
context = ssl.SSLContext(protocol)
context.set_ciphers('ALL')
context.check_hostname = False
context.verify_mode = ssl.CERT_REQUIRED
purpose = ssl.Purpose.SERVER_AUTH
context.load_verify_locations(cafile)

try:
    # build the initial socket
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to the SSL socket
    socket.connect((s_hostname, port))
    ssl_socket = context.wrap_socket(socket, server_hostname=s_hostname)
except:
   print ('Unable to connect to the server at: ' + s_hostname + ':' + str(port))
   exit(2)

# display the menu until valid menu options are
# selected and the program is complete
while True:

    # display a menu
    menuOption = displayMenu()
    
    # allow for the user t provide their credentials.
    if menuOption == '0':

        # performs simple validation of the username to ensure
        # that it is alphanumeric and that it is of the proper length.
        # The username is converted to lowercase for consistancy.
        while True:
            temp_username = input('User Name: ').lower()
            if  (len(temp_username) >= 5 and len(temp_username) <= 15 and temp_username.isalnum()):
                break
            else:
                print ('Username length is ' + str(len(temp_username)) + ' characters.')
                print ('Username must be between 6 and 15 characters.')

        # performs simple validation of the password to ensure
        # that it is alphanumeric and that it is of the proper length.
        # The username is converted to lowercase for consistancy.
        while True:
            temp_password = input('Password: ')
            if (len(temp_password) >= 6  and len(temp_password) <= 15 and temp_username.isalnum()):
                temp_password = hashlib.sha224(temp_password.encode('UTF-8')).hexdigest()
                break
            else:
                print ('Password length is ' + str(len(temp_password)) + ' characters.')
                print ('Password must be between 6 and 15 characters.')
        
        # username has been validated - so continue
        username = temp_username
        
        # password has been validated - so continue
        password = temp_password
                
        command = 'login:' + username + ':'+ password + '\n'
        numbytes = ssl_socket.send(command.encode(encoding_type))

        # get the authentication status
        status = ssl_socket.recv(1024).decode(encoding_type)
        
        if ("invalid:" in status):
           print ('Unable to authenticate your login.')
           authenticated = False
        else:
           authenticated = True
           print ('\nAuthentication complete.')
           
    # allow the user to upload a file to the server
    elif menuOption == '1' and authenticated:
        filename = input('File to upload: ')

        # validate that the file exists
        if os.path.exists(filename):

            # Tell the server that we are getting
            # ready to send the file. Include user
            # and password information
            command = 'sendtoserver:'+ username + ':'+ password + '\n'

            bytes_sent = ssl_socket.send(command.encode(encoding_type))
            
            # check that the server still authenticates
            # the user
            status = ssl_socket.recv(1024).decode(encoding_type)
        
            if ("invalid:" in status):
                print ('Unable to authenticate your login.')
                authenticated = False
                break
            else:
                authenticated = True
                print ('\nAuthentication complete.')
            
            # now tell the server the name of
            # the file that the client is sending
            ssl_socket.send((filename + '\n').encode(encoding_type))
            print ('Filename: ', filename)

            # now send to the server the size of the file.
            filesize = os.path.getsize(filename)
            ssl_socket.send(convert_to_bytes(filesize))

            # open and send the entire file
            # to the client 
            with open(filename, 'rb') as file_to_send:

                # Grab first 1024 bytes of the file
                data = file_to_send.read(1024)

                # while there is still data to send
                while data:

                    # send the data over the SSL socket
                    ssl_socket.send(data)
                     
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
    elif menuOption == '2' and authenticated:
       
        # build the command to be sent to the server
        command = 'downloadfromserver:'+ username + ':'+ password + '\n'

        # and send the command
        bytes_sent = ssl_socket.send(command.encode(encoding_type))

        # check that the server still authenticates
        # the user
        status = ssl_socket.recv(1024).decode(encoding_type)
        
        if ("invalid:" in status):
            print ('Unable to authenticate your login.')
            authenticated = False
            break
        else:
            authenticated = True
            print ('\nAuthentication complete.')

        # tell the server which file that
        # we want to download
        print ('File to download: ')
        filename = input()
        
        # send filename to download to the server
        ssl_socket.send((filename + '\n').encode(encoding_type))

        # get the filesize to expect
        filesize = ssl_socket.recv(4)               # selecting 4 bytes means that the file cannot be over 1 GB
        filesize = bytes_to_number(filesize)        # convert the bytes to an integer value

        # if the file is 0 bytes in size, the user selected a file that did not exist.
        if (filesize == 0):

            # tell the user that the file does not exist
            print ('File does not exist on the server!')
        else:
            # else we have a valid file and can proceed
            receivedAmount =  0

            # open a local file to store the new data
            with open(filename, 'wb') as file_to_write:

                # while there is more data to be received
                while receivedAmount < filesize:

                    # grab the data in 1024 byte chunks
                    data = ssl_socket.recv(1024)

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
    elif menuOption == '3' and authenticated:
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

        # build the command to be sent to the server
        command = 'shutdownsocket:'+ '\n'

        # and send the command
        ssl_socket.send(command.encode(encoding_type))
        
        # shutdown the socket
        ssl_socket.shutdown(1)

        # close the socket
        ssl_socket.close()
        break
    else:
        # tell the user that they need
        # to authenticate first
        if (authenticated is False):
            print ('Please login first.')
        else:
            # we received an invalid menu option.  Tell
            # user and rebuild the menu.
            print ('Invalid input!  Try again.')
