#!/usr/bin/python3
#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 3                   shawak@dukes.jmu.edu              #
#                              November15, 2015                 #
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
import os
import sys
import pickle
import time
import ssl
import hashlib
import getopt

from cloud import *

def main ():
   
   
                             
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
   
   if (not os.path.exists(cafile)):
      print ('cafile: ' + cafile + ' is missing.')
      print ("Exiting program.")
      sys.exit(1)
   else:
      context.load_verify_locations(cafile)

   try:
      opts, args = getopt.getopt(sys.argv[1:],"hu:p:c:",["username=","password=","client_id="])
   except getopt.GetoptError:
      client_usage()

   username=""
   password=""
   client_id = 0
   
   for opt, arg in opts:
      if opt == '-h':
         print ('cloud_client.py -u <username> -p <password> -c <client_id>')
         print ('   <username> must be alphanumeric between 5 and 15 characters')
         print ('   <password> must be alphanumeric between 6 and 15 characters')
         print ('   <client_id> must be an integer between 1 and 10000')
         sys.exit(2)
      elif opt in ("-u", "--username"):
         username = arg
      elif opt in ("-p", "--password"):
         password = arg
      elif opt in ("-c", "--client_id"):
         client_id = arg

   # performs simple validation of the client to ensure
   # that it is an integer less than 1000
   if  (not client_id.isnumeric() or int(client_id) < 1  or int(client_id) > 10000):
      print ('The client_id must be an integer between 1 and 1000')
      sys.exit ("Exiting program")

   # performs simple validation of the username to ensure
   # that it is alphanumeric and that it is of the proper length.
   # The username is converted to lowercase for consistancy.
   if  (len(username) < 5 or len(username) > 15 or not username.isalnum()):
      print ('Username length is ' + str(len(username)) + ' characters.')
      print ('Username must be between 6 and 15 characters.')
      sys.exit ("Exiting program")

   # performs simple validation of the password to ensure  
   # that it is alphanumeric and that it is of the proper length.
   # The username is converted to lowercase for consistancy.
   if (len(password) >= 6  and len(password) <= 15 and password.isalnum()):
      # Get a hash of the password and use it from here on
      password = hashlib.sha224(password.encode('UTF-8')).hexdigest()
   else:
      print ('Password length is ' + str(len(password)) + ' characters.')
      print ('Password must be between 6 and 15 characters.')
      sys.exit ("Exiting program")


   try:
      # build the initial socket
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  
      # connect to the SSL socket
      sock.connect((s_hostname, port))
  
      ssl_socket = context.wrap_socket(sock, server_hostname=s_hostname)
  
   except socket.error as msg:
      sys.stderr.write('[ERROR] :'+ msg[1] )
      print ('Unable to connect to the server at: ' + s_hostname + ':' + str(port))
      sys.exit(2)
         
   user_dir = username + '/'      
   if not os.path.exists(user_dir):
      os.makedirs(user_dir)

   authenticated = validate_user_password_input(client_id, ssl_socket, username, password)
   if not (authenticated):
      sys.exit('Unable to authenticate user: ' + username)
   
   path = username + '/'
   old_state = compute_dir_state(path)

   # Set up a monitor to check periodically if files need to 
   # be downloaded or uploaded from/to the server in order
   # to keep the user's local directory in sync with the server
   while True:
     
      # Run through this loop every 5 seconds
      # this could be easily placed in to an
      # initialization file if needed
      time.sleep(5)
      
      # Determine the current state of the client's
      # files on this particular computer
      new_state =  compute_dir_state(path)
      
      # Determine what has changed since the last time
      # we looked at the filestate.
      data = compute_diff(new_state, old_state)  
      
      # means local file is new    
      for f in data['on_server_not_client']:
          print('<<Send on_server_not_client command for:>>' + f)
      
      # means local file has been deleted 
      for f in data['on_client_not_server']:
          print('Send delete from server command for: ' + f)
          delete_file_from_server(ssl_socket, username, password, username +'/'+ f)
          
      # make the new state the old state for 
      # future checks
      old_state = new_state
       
      # Periodically, send the client filestate to the server
      if (not validate_user_password_input(client_id, ssl_socket, username, password)):
         print ("System error!")
         break
      

      # Build the filename for the server filestate.
      filename = username + '_filestate_server.bin'      
      old_filename = filename + '.old'
      
      if os.path.exists(filename):
         # copy the old filestate file from the server to .old 
         os.rename(filename, old_filename)     
         
      # download the server's file state for this particular user
      if not receive_file_from_server(ssl_socket, username, password, filename):       
         print ('>>>File Receive Error<<' + filename)
         sys.exit(2)
         
      # don't compare if this is the first time that
      # we have checked the server file state.
      if os.path.exists(old_filename):
         
         # compare filestate_server.bin with filestate_server.bin.old
         filestate = compare_server_state_files(username)
         
         # means local file is new    
         for f in filestate['on_server_not_client']:
            print('>>Send on_server_not_client command for:<<' + f)
      
         # means server file has been deleted 
         for f in filestate['on_client_not_server']:
            print('File deleted from the server: ' + f)
            
            file_path = (username +'/' + f)
            # We need to delete the local 
            # copy of the file
            if os.path.exists(file_path):
               os.remove(file_path) 
               print('---' + file_path + ' deleted from the client.')
               # update the current filestate for 
               # this client's local computer
               build_state_file(client_id, username, CLIENT)
               
      # Check latest differences between the client and the server
      filestate = extract_state_file(client_id, username, CLIENT)
      #print (filestate)
      
      # if we are the client, we can now issue
      # commands to upload or download updated 
      # files to/from the server. File deletions
      # are handled as well
      for f in filestate['newer_on_server']:
         print('Download from server: ' + f)
         if (not receive_file_from_server(ssl_socket, username, password, f)):
            break

      for f in filestate['newer_on_client']:
         print('Download from server: ' + f)

         # send the file to the server
         send_file_to_server(ssl_socket, username, password, username +'/'+ f)

   
      for f in filestate['on_server_not_client']:
         print('Download from server: ' + f)
   
         if (not receive_file_from_server(ssl_socket, username, password, f)):
            break
 
      for f in filestate['on_client_not_server']:
         print('Upload to server: ' + f)

         # send the file to the server
         send_file_to_server(ssl_socket, username, password, username +'/'+ f)

      

if __name__ == "__main__":
    main()
                
