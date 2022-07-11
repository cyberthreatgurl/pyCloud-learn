#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 2                   shawak@dukes.jmu.edu              #
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
import threading
import sys
import os
import time
import ssl
import hashlib
import shutil

# function to validate a given directory's 
# existance.  Will create it if the directory
# does not already exist.
def validate_directory(temp_directory):

   # perform simple validation and santization of file
   # to ensure directories exist for created users
   if not os.path.exists(temp_directory):
      print ('Error:  Directory for existing user ' + temp_directory + ' does not exist.')
      return False
   else:
      return True         
            
# function to check the password file for
# the user's account information
def validate_user(tmp_username,tmp_password):

   filename = 'user_db'
  
   if not os.path.exists(filename):
      print ('Error:  User database does not exist.')
      exit(1)
          
   username=[]   # initialize user list
   password=[]   # initialize password list

   # Open password file for reading and
   # read entire password file into 
   # username/password array for update   
   with open(filename, 'r') as password_file:      
      
      # read the first line of the file
      line = password_file.readline()
      
      # while the file is not empty
      # keep reading lines 
      while line:
         
         # remove the end of line character
         line = line.rstrip('\n')
         
         # parse the line 
         sout = line.split(':')

         # store each element in an arrary
         username.append(sout[0])
         password.append(sout[1])
         
         # check to see if the user's directory exists
         # and create it if not.  But, if it cannot be
         # created, we have a problem Houston.  Let's
         # shut down operations.
         if not validate_directory(sout[0]):
            exit(3)

         # if we have read in the current user
         # validate the password entered
         if (sout[0] == tmp_username):
            if (sout[1] == tmp_password):
               return True
            else:
               return False
                     
         # read the next line from the file
         line = password_file.readline()
         
      # close the file.
      password_file.close()   
   
      
   
   # close the file
   password_file.close()

# convert bytes to a integer			
# used to pull the filesize
# from the socket message
def convert_to_bytes(number):
    bytesvalue = bytearray()
    bytesvalue.append(number & 255)
    for i in range(3):
        number = number >> 8
        bytesvalue.append(number & 255)
    return bytesvalue

# convert integer to bytes			
# used to pull the filesize
# from the socket message
def bytes_to_number(bytesvalue):
    number = 0
    for i in range(4):
        number += bytesvalue[i] << (i*8)
    return number

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
               print ('Authenticated username: ' + username)
               auth_status = 'authenticated:'
            else:
               print ('Invalid user: ' + username)
               auth_status = 'invalid:'
               
            # send the authenticate status message back to the client
            client_socket.send((auth_status + username + '\n').encode(encoding_type))
       
        elif (command.find('sendtoserver:') != -1):
            cmd, username, password = command.split(':')
            
       
            if validate_user(username, password):
               print ('Authenticated username: ' + username)
               auth_status = 'authenticated:'
            else:
               print ('Invalid user: ' + username)
               auth_status = 'invalid:'
               
            # send the authenticate status message back to the client
            client_socket.send((auth_status + username + '\n').encode(encoding_type))
            
            
            #filename = client_socket.recv(128).decode(encoding_type)
            filename = socketfile.readline()[:-1]
      
            # Determine the size of the file that we are
            # getting ready to receive

            filesize = client_socket.recv(4)       # selecting 4 bytes  means that the file cannot be over 1 GB in size
            filesize = bytes_to_number(filesize)   # unpack the bytes to determine actual integer value

            # set up a loop to keep receiving data while
            # there is more left in the file to receive
            receivedAmount =  0
      
            try:
                
                # build the file storage path to 
                # include the username
                filename = username + '/' + filename
                #open the local file for write
                with open(filename, 'wb') as file_to_write:
                    # while the entire file has not been received
                    while receivedAmount < filesize:
                    
                        #grab 1024 bytes at a time
                        data = client_socket.recv(1024)
                        
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

                    # print to the server console a status update
                    print ('Received: ' + filename + ' from ' + username + '\n')
         
                    # and close the file when complete
                    file_to_write.close()
               
            except IOError as err:
                errno, strerror = err.args
                print("I/O error({0}): {1}".format(errno, strerror))
             
        # if the client would like to download a file
        elif (command.find('downloadfromserver:') != -1):
            cmd, username, password = command.split(':')
            
            print ('downloadfromserver: authenticated username: ' + username )
       
            if validate_user(username, password):
               print ('Authenticated username: ' + username)
               auth_status = 'authenticated:'
            else:
               print ('Invalid user: ' + username)
               auth_status = 'invalid:'
               
            # send the authenticate status message back to the client
            client_socket.send((auth_status + username + '\n').encode(encoding_type))
                  
            # wrap the socket in an object file
            sockfile = client_socket.makefile('r')   
            
            # we should receive the filename right
            # after the command is received
            filename = sockfile.readline()[:-1]

            # build the file storage path to 
            # include the username
            filename = username + '/' + filename
            
            # check to see if we received a valid filename
            # and if it even exists
            if (os.path.exists(filename)):
                print ('Preparing to send:' + filename)
        
                # now send to the client the size of the file.
                filesize = os.path.getsize(filename)
                client_socket.send(convert_to_bytes(filesize))

                # open and send the entire file
                # to the client 
                with open(filename, 'rb') as file_to_send:
                    data = file_to_send.read(1024)
                    while data:
                        client_socket.send(data)
                        data = file_to_send.read(1024)
                           
                    # print to the server console a status update
                    print ('Sent: ' + filename + ' to ' + username + '\n')
               
                    file_to_send.close()
            else:
                # File does not exist, so let's send the client
                # a filesize of zero, so it can alert the user
                filesize = 0
                client_socket.send(convert_to_bytes(filesize))

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
