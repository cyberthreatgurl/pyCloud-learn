Code written by A. Kelly Shaw <cyberintelgurl@gmail.com>
Feel free to copy, modify, and otherwise use to help you learn.

I do NOT claim to be an expert Python coder. I know just enough to be
dangerous..uh...make it do what I want it to do!

Kelly Shaw
July 11, 2022

# pyCloud-learn
A very, very basic iteration of a client-server cloud arrangement built using Python 3

This project is a modified version of what I previously built for a Masters class
on Networking and Security.  It is a simple (very simple) cloud server/client arrangement
along the lines of a very primitive Dropbox or iCloud drive.  It demonstrates
basic TCP/IP socket usage along with encryption and file synching capabilities.

# Version 1 Goal
Build a file server that works over the network. Ensure that it allows the user to upload 
and download files. Make sure that if the file already exists on the server that it is overwritten. 
Also, ensure that an error is generated if the file does not exist on the server.

# Version 2 Goal
Upgrade the basic cloud server and client program Version 1.  These upgrades include, but are not 
limited to, support for an SSL connection to the server as well as multiple user accounts.

# Version 3 Goal
Add support for enhanced security and file sharing among users. Files will only be stored on the 
server in encrypted form using a key the server does not know. Therefore, if the server is 
compromised, a user’s files are not. Note that the files will be stored in unencrypted form 
on each of the client’s computers but never on the server.  Implement file sharing so that a 
user can specify that a particular file in his or her cloud storage should be shared with other users.

