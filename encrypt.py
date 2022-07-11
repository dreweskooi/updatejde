import base64
import socket
import sys
#hostname = socket.gethostname()
#print(hostname)
if len(sys.argv) == 3:
    if int(sys.argv[1])==1:
        inputString= sys.argv[2]
        base64Value = base64.b85encode(inputString.encode())
        print("Encrypted string:")
        print(str(base64Value))
    exit(0)
#Taking input through the terminal.
welcomeInput= input("Enter 1 to encrypt String, 2 to decrypt to String(anything else will exit) : ") 
try:
    if(int(welcomeInput)==1 or int(welcomeInput)==2):
        #Code to Convert String to Base 85.
        if int(welcomeInput)==1:
            inputString= input("Enter the String to be encrypted:") 
            base64Value = base64.b85encode(inputString.encode())
            print(str(base64Value))
        #Code to Convert Base 64 to String.
        elif int(welcomeInput)==2:
            inputString= input("Enter the value to be decrypted:")
            stringValue = base64.b85decode(inputString[2:-1])
            print("Value = ",str(stringValue)[2:-1])
except Exception as ex:
    print('No valid response!')
finally:
    print("Exiting")