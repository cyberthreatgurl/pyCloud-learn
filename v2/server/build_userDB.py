#################################################################
# CS - 610                     Kelly Shaw                       #
# Project 2                   shawak@dukes.jmu.edu              #
#                              October 25, 2015                 #
# Simple File Server Implementation                             #
#                                                               #
# filename:  build_userdb.py                                    #
#                                                               #
# This program is an interface in to building the username      #
# and password file.  It allows the administrator to add new    #
# Usernames and passwords to the file.  It performs a simple    #
# sha224 hash of the password and stores it in the file.  No    #
# salts are added to this very basic password file.             #
# This password will automatically create the users directory   #
# if it does not already exist.                                 #
#                                                               #
# Requires:   Python3                                           #
# Tested on:  Windows 10, Ubuntu 14.04.3 LTS                    #
#                                                               #
# Version:  1.0       AKS       October 25, 2015                #
#               - Basic implemention of username/password file. #
#                 authentication.  Also, a simple TLSv1.2       #
#                 session encryption has been added.            #
#                                                               #
#                                                               #
#################################################################
import sys
import hashlib
import getpass
import os
import shutil


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
            
# main function to handle password file creation            
def main():
  
   #point to the user database file
   filename = 'user_db'

     
   # make sure that we are in the correct folder
   path = os.getcwd()
   if 'proj2/server' not in path:
      print ('Software not installed correctly.')
      exit (2)
  
      
   # before opening old password
   # file, lets back it up to user_db.orig
   backup_filename = 'user_db.orig'
  
   username=[]   # initialize user list
   password=[]   # initialize password list
      
   if os.path.exists(filename):
      shutil.copy2(filename, backup_filename)
         

      print ('\nCloud User Admin Tool')
      print ('----------------------')	
   
   


      # if file does not exist, create it.
      # otherwise open it for reading and
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
            # shutdown
            if not validate_directory(sout[0]):
               print ('got here')
               exit(3)
            
            # read the next line from the file
            line = password_file.readline()
         
         # close the file.
         password_file.close()   

   
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
      
         

   # does the username already exist?
   
   if temp_username in username:
      duplicate = True
      
      # update the password
      index = username.index(temp_username)
      password[index] = temp_password
      print ('Username exists - password updated.')
   else:
      # since the username does not exist
      # append it to the username/password array
      duplicate = False
      
      # add the new username and
      # password to the lists
      username.append(temp_username)
      password.append(temp_password)
      
      # tell the user that we've added a new user
      print ('New User created.')
      
     
      
   # Check to see if the users directory
   # already exists, if not, create it.
   if not validate_directory(temp_username):
      exit(3)
      
            
   # write the whole array out to file
   with open(filename, 'w') as password_file:
      
      # write the entire username/password lists
      # to the new password file
      for i in range(len(username)):
         # build each line one at a time
         line = username[i] + ':' + password[i] + '\n'
         
         # write the line to a file
         password_file.write(line)
   
   
   # close the file
   password_file.close()

			
if __name__ == "__main__":
   main()


