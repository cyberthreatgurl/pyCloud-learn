#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 3                    shawak@dukes.jmu.edu             #
#                              November15, 2015                 #
# Simple File Server Implementation                             #
#                                                               #
# filename:  cloud.py                                           #
#                                                               #
# This module implements many of the client/server functions    #
# that are used in the cloud server.                            #
#                                                               #
# Requires:   Python3                                           #
# Tested on:  Ubuntu 14.04.3 LTS                                #
#                                                               #
# Version:  1.0        AKS       November 13, 2015              #
#               - Basic implementation of a cloud server with   #
#                 synchronization between multiple computers    #   
#                 for multiple users.                           #
#                                                               #
#################################################################
import os
import socket
import threading
import sys
import os
import time
import ssl
import pickle
import hashlib

encoding_type = 'utf-8'
SERVER = 'server'
CLIENT = 'client'

# This function will request a specific file from the server
# and then receive it. Authentication is performed first to 
# ensure that user is properly recognized.
def receive_file_from_server(socket, user_name, pass_word, file_name):
   # build the command to be sent to the server
   command = 'downloadfromserver:'+ user_name + ':'+ pass_word + '\n'

   # and send the command
   bytes_sent = socket.send(command.encode(encoding_type))

   # check that the server still authenticates
   # the user
   status = socket.recv(1024).decode(encoding_type)
        
   if ("invalid:" in status):
      print ('Unable to authenticate your login.')
      authenticated = False
      return False
   else:
      authenticated = True
      #print ('\nAuthentication complete.')

        
   # send filename to download to the server
   socket.send((file_name + '\n').encode(encoding_type))

   # get the filesize to expect
   filesize = socket.recv(4)               # selecting 4 bytes means that the file cannot be over 1 GB
   filesize = bytes_to_number(filesize)    # convert the bytes to an integer value

   # wrap the socket in an object file
   sockfile = socket.makefile('r')  
   
   # get the last modified time of the file
   lmtime = sockfile.readline()[:-1]
   
   # if the file is 0 bytes in size, the user selected a file that did not exist.
   if (filesize == 0):

      # tell the user that the file does not exist
      print ('File does not exist on the server!')
      return False
   else:
      # else we have a valid file and can proceed
      receivedAmount =  0
      
      # we need to store the filestate file from the
      # server in the root folder and NOT the user's directory
      if (file_name.find('_filestate_server.bin') == -1):
         file_name = user_name + '/' + file_name
         
      # open a local file to store the new data
      with open(file_name, 'wb') as file_to_write:

         # while there is more data to be received
         while (receivedAmount < filesize):

            # grab the data in 1024 byte chunks
            data = socket.recv(1024)

            # if no more data, we are done
            if not data:
               break

            # determine if we've received all of the file contents
            if ((len(data) + receivedAmount) < filesize):

               # add the new data to the buffer
               data = data[:filesize-receivedAmount]
               
            # increment our data received counter
            receivedAmount += len(data)

         
            try:
               # and we can write the data to the local file
               file_to_write.write(data)
         
            except IOError:
               print ('Error: Unable to write to the file: '+file_name)
               return False
   
         # close the file
         file_to_write.close()
         
         # update last modified_time_of the file
         os.utime(file_name, (float(lmtime), float(lmtime)))
         
         # print to the server console a status update
         print ('Received: ' + file_name + ' ('+ str(receivedAmount) + ' bytes) from ' + user_name + '\n')

         return True

# This function will receied specific file from the client
# Authentication is performed first to  ensure that user is 
# properly recognized.
def receive_file_from_client(socket_file, socket, user_name, pass_word):
   # initialize the filename
   filename = ""
   
   if validate_user(user_name, pass_word):
      print ('Authenticated username: ' + user_name)
      auth_status = 'authenticated:'
   else:
      print ('Invalid user: ' + user_name)
      auth_status = 'invalid:'
               
   # send the authenticate status message back to the client
   socket.send((auth_status + user_name + '\n').encode(encoding_type))
            
   # Get the filename from the client            
   filename = socket_file.readline()[:-1]
      
   # Determine the size of the file that we are
   # getting ready to receive

   filesize = socket.recv(4)              # selecting 4 bytes  means that the file cannot be over 1 GB in size
   filesize = bytes_to_number(filesize)   # unpack the bytes to determine actual integer value

   # get the last modified time from the client
   lmtime = socket_file.readline()[:-1]
 
   # set up a loop to keep receiving data while
   # there is more left in the file to receive
   receivedAmount =  0

   try:
      
      #open the local file for write
      with open(filename, 'wb') as file_to_write:
         # while the entire file has not been received
         while receivedAmount < filesize:
                
            #grab 1024 bytes at a time
            data = socket.recv(1024)
            
            # we received something doesn't look
            # right, let's break out of this loop            
            if not data:
               break
               
            #if don't have the complete file yet, keep
            # receiving data
            if ((len(data) + receivedAmount) < filesize):
               # keep totalling the amount of data that has been received
               data = data[:filesize-receivedAmount]
               
            # total up the amount of data received so far
            receivedAmount += len(data)

            # write the data to the local file
            file_to_write.write(data)

         # print to the server console a status update
         print ('Received: ' + filename + ' from ' + user_name + '\n')
         
         # and close the file when complete
         file_to_write.close()
         
         # update last modified_time_of the file
         os.utime(filename, (float(lmtime), float(lmtime)))
         
         return filename
               
   except IOError as err:
      errno, strerror = err.args
      print("I/O error({0}): {1}".format(errno, strerror))

def delete_file_from_server(socket, username, password, filename_to_delete):
   # Tell the server that we are getting
   # ready to send the file. Include user
   # and password information
   command = 'deletefromserver:'+ username + ':'+ password + '\n'
   socket.send(command.encode(encoding_type))
            
   # check that the server still authenticates
   # the user
   status = socket.recv(1024).decode(encoding_type)
  
   if ("invalid:" in status):
      print ('Unable to authenticate your login.')
      authenticated = False
      #break
   else:
      authenticated = True
      print ('\nUser: '+username+' logged in.')
           
      # now tell the server the name of
      # the file that the client is sending
      socket.send((filename_to_delete + '\n').encode(encoding_type))


# Sends a file to the server
def send_file_to_server(socket, username, password, filename_to_send):

   # validate that the file exists
   if os.path.exists(filename_to_send):

      # Tell the server that we are getting
      # ready to send the file. Include user
      # and password information
      command = 'sendtoserver:'+ username + ':'+ password + '\n'

      bytes_sent = socket.send(command.encode(encoding_type))
            
      # check that the server still authenticates
      # the user
      status = socket.recv(1024).decode(encoding_type)
        
      if ("invalid:" in status):
         print ('Unable to authenticate your login.')
         authenticated = False
         #break
      else:
         authenticated = True
         print ('\nUser: '+username+' logged in.')
            
         # now tell the server the name of
         # the file that the client is sending
         socket.send((filename_to_send + '\n').encode(encoding_type))

         # now send to the server the size of the file.
         filesize = os.path.getsize(filename_to_send)
         socket.send(convert_to_bytes(filesize))

         # now send the last modified time of
         # the file to the sever for continuity sake
         lmtime = os.stat(filename_to_send).st_mtime

         socket.send((str(lmtime)+ '\n').encode(encoding_type))
         
         # open and send the entire file
         # to the client 
         with open(filename_to_send, 'rb') as file_to_send:

            # Grab first 1024 bytes of the file
            data = file_to_send.read(1024)

            # while there is still data to send
            while data:

               # send the data over the SSL socket
               socket.send(data)
                     
               #grab more data and interate
               data = file_to_send.read(1024)

            # We are finished sending the file.
            # Issue an alert to the console.
            print ('Sent ' + filename_to_send + ' to the server.')

            # close the file.
            file_to_send.close()
   else:
      # the user picked a nonexistent file.
      print ('file ' + filename_to_send + ' does not exist! Check case and try again.')

# this function sends a file to the client
def send_file_to_client(socket, user_name, pass_word, status):
   # Session ID is not defined on the server
   tmpSessionID = 0
   
   print ('downloadfromserver:  username: ' + user_name )
       
   if validate_user(user_name, pass_word):
      auth_status = 'authenticated:'
   else:
      print ('Invalid user: ' + user_name)
      auth_status = 'invalid:'
      return False
    
   # send the authenticate status message back to the client
   socket.send((auth_status + user_name + '\n').encode(encoding_type))
                  
   # wrap the socket in an object file
   sockfile = socket.makefile('r')   
            
   # we should receive the filename right
   # after the command is received
   filename = sockfile.readline()[:-1]

    
   # If the client wants to check the server's 
   # file status, build the status and then send it
   if (filename.find('_filestate_server.bin') != -1 or (status == 'file_state')):
      build_state_file(tmpSessionID, user_name, SERVER)
   else:  
      filename = user_name + '/' + filename
            
   # check to see if we received a valid filename
   # and if it even exists
   if (os.path.exists(filename)):
        
       # now send to the client the size of the file.
       filesize = os.path.getsize(filename)
       socket.send(convert_to_bytes(filesize))

       # now send the last modified time of
       # the file to the sever for continuity sake
       lmtime = os.stat(filename).st_mtime

       socket.send((str(lmtime)+ '\n').encode(encoding_type))
          
       sentAmount = 0
       # open and send the entire file
       # to the client 
       with open(filename, 'rb') as file_to_send:
           data = file_to_send.read(1024)
           while data:
               socket.send(data)
               # total up the amount of data sent so far
               sentAmount += len(data)
      
               data = file_to_send.read(1024)
      
       file_to_send.close()
                           
       # print to the server console a status update
       print ('Sent  ' + filename + ' ('+ str(sentAmount) + ' bytes) to ' + user_name + '\n')

   else:
       # File does not exist, so let's send the client
       # a filesize of zero, so it can alert the user
       filesize = 0
       socket.send(convert_to_bytes(filesize))
   
   return True    

# function to validate a given directory's
# existance.  Will create it if the directory
# does not already exist.
def validate_directory(temp_directory):

   # perform simple validation and santization of file
   # to ensure directories exist for created users
   if not os.path.exists(temp_directory):
      print ('Error:  Directory for existing user ' + temp_directory + ' does not exist.')
      try:
         os.makedirs(temp_directory)
         print ('Directory ' + temp_directory + ' created.')
         return True
      except:
         print ('Error:  unable to create folder for user ' + temp_directory )
         return False
   return True       

# this function adds up all of the folder and files
# in a given starting path.
def compute_dir_state(path):
   files = []
   subdirs = []

   # cycle through all of the file and directories
   # in the passed in path....a user's folder
   for root, dirs, filenames in os.walk(path):
      # grab all of the subdirectories that may exist
      # however, we haven't really designed for subfolders
      # in a users folder.
      for subdir in dirs:
         subdirs.append(os.path.relpath(os.path.join(root, subdir), path))

      # grab all of the filenames in the folders
      for f in filenames:
         files.append(os.path.relpath(os.path.join(root, f), path))

      i = 0
      index = {}
      for f in files:
         # get the last modified times to be used later
         index[f] = os.path.getmtime(os.path.join(path, files[i]))
         i +=1

   return dict(files=files, subdirs=subdirs, index=index)
   
   
def compute_diff(state_new, state_old):
    data = {}
    data['on_client_not_server'] = list(set(state_old['files']) - set(state_new['files']))
    data['on_server_not_client'] = list(set(state_new['files']) - set(state_old['files']))
    data['newer_on_server'] = []
    data['newer_on_client'] = []
    data['deleted_users'] = list(set(state_old['subdirs']) - set(state_new['subdirs']))
    data['created_users'] = list(set(state_new['subdirs']) - set(state_old['subdirs']))
    
    # cycle through all of the files for a particular user
    for f in set(state_old['files']).intersection(set(state_new['files'])):
        
        # Check the last modified date if it is newer on the
        # server version of the file, put this file in the
        # appropriate array for action
        if state_new['index'][f] > state_old['index'][f]:
            data['newer_on_server'].append(f)
        
        # Check the last modified date if it is newer on the
        # client version of the file, put this file in the
        # appropriate array for action
        elif state_new['index'][f] < state_old['index'][f]:
            data['newer_on_client'].append(f)
         
    return data
 
# main function to handle password file creation
def build_state_file(sessionID, username, location):

   # Define the path to the directory
   # that we want to track
   path = username + '/'

   # Build the filename based on whether it is the client
   # or the server
   if (location == SERVER):
      state_file_name = username + '_filestate_'+location+'.bin'
   else:
      state_file_name = username + '_' + str(sessionID) + '_filestate_'+location+'.bin'
   
   # compute the filestate
   new_state =  compute_dir_state(path)
   
   
   try:
      # open the filestate.bin file for writing
      state_file = open(state_file_name, 'wb')
   except IOError as e:
      errno, sterror = e.args
      print ("I/O Error ({0}):  {1}".format(errno, strerror))
      return False
      
   # use pickle to dump the state list to the file 
   # in binary format
   pickle.dump(new_state, state_file)
   
   # close the file 
   state_file.close()
   
   return True  

# main function to extract user file state file
# back to list for operations
def compare_server_state_files(username):

   # build filenames
   current_server_state_file_name = username+ '_filestate_server.bin'
   old_server_state_filename =  current_server_state_file_name + '.old'
   
   # get file handles to state files
   old_state_file = open(old_server_state_filename, 'rb')
   new_state_file = open(current_server_state_file_name, 'rb')
   
   # Use pickle to read the date back in to a list
   try:      
      old_state = pickle.load(old_state_file)
   except:
      print ('error opening ' + old_state_file)
      old_state = []
    
   # Use pickle to read the date back in to a list
   try:      
      new_state = pickle.load(new_state_file)
   except:
      print ('error opening ' + new_state_file)
      new_state = []

   # close the state files
   old_state_file.close()
   new_state_file.close()
   
   data = compute_diff(new_state, old_state)      
            
   return data
   
   
# main function to extract user file state file
# back to list for operations
def extract_state_file(sessionID, username, location):

   path = username + '/'
   client_state_file_name = username + '_' + str(sessionID) + '_filestate_client.bin'
   server_state_file_name = username + '_filestate_server.bin'

   # read filestate in to local file
   client_state_file = open(client_state_file_name, 'rb')
   server_state_file = open(server_state_file_name, 'rb')
   
   # Use pickle to read the date back in to a list
   try:      
      client_state = pickle.load(client_state_file)
   except:
      print ('error opening ' + client_state_file)
      client_state = []
    
   # Use pickle to read the date back in to a list
   try:      
      server_state = pickle.load(server_state_file)
   except:
      print ('error opening ' + server_state_file)
      server_state = []

   # close the state files
   client_state_file.close()
   server_state_file.close()
   
   data = compute_diff(server_state, client_state)      
            
   return data
      
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
      
   
def client_usage():
   print ("CS-610 Cloud Client")
   
   print ("Usage: python3 cloud_client.py -u user_name -p password -c client_id\n")
 
   print ("Example:")
   print ("python3 cloud_client.py -u willy -p fake_password -c 992")
   exit(1)
   

# This function validates the username and password hash
# as computed from passed in arguments.  It also sends
# a _filestate_client.bin packet to the server.  
def validate_user_password_input(sessionID, socket, user_name, pass_word):
   
   # build the login command for the server             
   command = 'login:' + user_name + ':'+ pass_word + '\n'
   
   # send the command to the server
   socket.send(command.encode(encoding_type))

   # get the authentication status
   status =  socket.recv(1024).decode(encoding_type)
        
   if ("invalid:" in status):
      return False
   
   # Upload the filestate_client to see if the server
   # needs to perform any updates to me
   build_state_file(sessionID, user_name, CLIENT)

   # send the filestate packet to the server
   send_file_to_server(socket, user_name, pass_word, user_name +'_'+ str(sessionID) + '_filestate_client.bin')
   
   
   return True

   

