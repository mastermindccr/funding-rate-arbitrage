import os
from dotenv import load_dotenv

load_dotenv()

# shift right
apiKey = os.getenv('API_KEY')
# shift left
secret = os.getenv('SECRET')

def byte_xor(ba1, ba2):
    return bytes([_a ^ _b for _a, _b in zip(ba1, ba2)])

def encrypt(data, file_bytes, direction):
    if direction == 'right':
        tmp = b''
        shift = file_bytes
        count = 0
        for i in file_bytes:
            tmp += i.to_bytes(1, 'big')
            count+=1
            if count==len(data):
                shift = byte_xor(shift, tmp)
                count = 0
                tmp = b''
        while(len(tmp)<len(data)):
            tmp += b'\x00'
        shift = byte_xor(shift, tmp)
        result = ''
        for x in zip(data, shift):
            target = x[0]

            # shift first
            target += x[1]
            while target>122:
                target -= 75
            
            # then check if it is alphanumeric
            while not chr(target).isalnum():
                target += x[1]
                while target>122:
                    target -= 75
            result += chr(target)
    else:
        tmp = b''
        shift = file_bytes
        count = 0
        for i in file_bytes:
            tmp += i.to_bytes(1, 'big')
            count+=1
            if count==len(data):
                shift = byte_xor(shift, tmp)
                count = 0
                tmp = b''
        while(len(tmp)<len(data)):
            tmp += b'\x00'
        shift = byte_xor(shift, tmp)
        result = ''
        for x in zip(data, shift):
            target = x[0]

            # shift first
            target -= x[1]
            while target<48:
                target += 75
            
            # then check if it is alphanumeric
            while not chr(target).isalnum():
                target -= x[1]
                while target<48:
                    target += 75
            result += chr(target)
    return result

with open('./main.py', 'rb') as file:
    file_bytes = file.read()
    new_apiKey = encrypt(apiKey.encode(), file_bytes, 'right')
    new_secret = encrypt(secret.encode(), file_bytes, 'left')
    print(new_apiKey)
    print(new_secret)