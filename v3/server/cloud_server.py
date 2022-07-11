#!/usr/bin/python3
#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 3                   shawak@dukes.jmu.edu              #
#                              October 25, 2015                 #
# Simple File Server Implementation                             #
#                                                               #
# filename:  cloud_server.py                                    #
#                                                               #
# This program implements the server side of the file server.   #
# It responds to "commands" issued from up to 5 clients.        #
# Usernames and passwords are stored on the server in a flat    #
# text file.  The passwords are encrypted and ony the hashes    #
# are stored. The server responds to download and upload        #
# User and session authentication is performed at very basic    #
# levels.                                                       #
# Requires:   Python3                                           #
# Tested on:  Ubuntu 14.04.3 LTS                                #
#                                                               #
# Version:                                                      #
#           3.0        AKS       November 14, 2015              #
#               - Support added for auto-sync of folders        #
#                 to multiple clients. Menu is no longer        #
#                 implemented.                                  #
#                                                               #
#           2.0        AKS       October 25, 2015               #
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
import threading
import sys
import os
import time
import ssl
import pickle
from cloud import *

# function that handles the different
# commands that may be received from the client
def handle_client (client_socket):
    # determine the encoding type of the local system
    encoding_type = sys.getfilesystemencoding()

    while True:
    
        # require authentication for each command
        authenticated = False
   
        # wait for a command from the client
        #  command = client_socket.recv(32).decode(encoding_type)
        socketfile = client_socket.makefile('r')
        command = socketfile.readline()[:-1]
      
        # if the client is trying to login
        # split out the username and password
        if ('login:' in command):
            cmd, username, password = command.split(':')
       
            if validate_user(username, password):
               auth_status = 'authenticated:'
            else:
               print ('Invalid user: ' + username)
               auth_status = 'invalid:'
               
            # send the authenticate status message back to the client
            client_socket.send((auth_status + username + '\n').encode(encoding_type))
       
        elif (command.find('sendtoserver:') != -1):
            cmd, username, password = command.split(':')

            filename = receive_file_from_client(socketfile, client_socket, username, password)
            
        elif (command.find('deletefromserver:') != -1):
            cmd, username, password = command.split(':')

            # initialize the filename
            filename = ""
   
            if validate_user(username, password):
               auth_status = 'authenticated:'
            else:
               print ('Invalid user: ' + usernname)
               auth_status = 'invalid:'
               
            # send the authenticate status message back to the client
            client_socket.send((auth_status + username + '\n').encode(encoding_type))
            
            # Get the filename from the client            
            filename = socketfile.readline()[:-1]
           
            # check to see if the file exists
            # before attempting to delete it 
            if (os.path.exists(filename)):
               # delete the file
               os.remove(filename)
           
            print ('Received file delete request from ' + username + ' for ' + filename)
            
           
        # if the client would like to download a file
        elif (command.find('downloadfromserver:') != -1):
            cmd, username, password = command.split(':')
            
            status = "normal"
            # send the file
            if (not send_file_to_client(client_socket, username, password, status)):
               print ("Error: unable to send file to client.")
               client_socket.shutdown(1)
               client_socket.close()
               
        # we have been told to shut down the server
        elif command == 'shutdownsocket:':
            print ('Client is disconnected.')
            
            client_socket.close()
        # handle weird or unexpected input
        else:
            print ('Not sure what I received. Closing socket.')

            # clean up and exit
            client_socket.shutdown(1)
            client_socket.close()
            exit(1)

def main ():

   # determine the encoding type of the local system
   encoding_type = sys.getfilesystemencoding()

   # Set the port number
   server_port = 5077

   # limit the number of connections to 1
   max_server_connections = 5

   # define the hostname of the server
   host = 'localhost'

   # build the SSL connection/purpose
   cafile=None
   certfile='localhost.pem'
   purpose = ssl.Purpose.CLIENT_AUTH
   context = ssl.create_default_context(purpose, cafile=cafile)

  
   if (not os.path.exists(certfile)):
      print ('certfile: ' + certfile + ' is missing.')
      print ("Exiting program.")
      sys.exit(1)
   else:
      context.load_cert_chain(certfile)

   # create a TCP/IP socket
   sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

   server_address =  (host, server_port)

   sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

   # bind the socket to the IP address and port
   try:
      sock.bind(server_address)
   except socket.error as e:
      print(str(e))

   # tell to the socket to listen for connections
   sock.listen(max_server_connections)
   print ('starting up on %s port %s' % server_address)
   print ('waiting for a connection...')

   # set up a loop to keep processing input  
   # and spin off a multitude of threads
   while True:
      # tell the socket to accept any connections
      (client, (client_address, client_port)) = sock.accept()

      # print an alert to the console to indicate a user has connected
      print ('Connection from: ' + client_address + ':' + str(client_port) + '\n')
   
      # buid the actual SSL socket
      ssl_sock = context.wrap_socket(client, server_side=True)
   
      # build and start the threads
      client_handler = threading.Thread(target=handle_client,args=(ssl_sock,))
      client_handler.start()
   

if __name__ == "__main__":
   main()
