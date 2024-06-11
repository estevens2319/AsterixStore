import socket
import json
import threading

def tests():
    backend = 'localhost'
    backendOrderPort1 = 1115
    backendOrderPort2 = 1116
    backendOrderPort3 = 1117
    
    # Check if placing an order for an in stock item works
    s = socket.socket()
    product = "place_order tux 2"
    s.connect((backend, backendOrderPort3)) 
    s.send(product.encode())
    response = s.recv(1024).decode()
    s.close()
    if(not 'error' in response):
        print("SUCCESS: Normal order works:", response)
    else:
        print("FAIL: Normal order issue:", response)

    # Check if placing an order for a non existant item returns an error
    s = socket.socket()
    product = "place_order CS677 2"
    s.connect((backend, backendOrderPort3)) 
    s.send(product.encode())
    response = s.recv(1024).decode()
    s.close()
    if('error' in response):
        print("SUCCESS: Non existant item order works:", response)
    else:
        print("FAIL: Non existant item order issue:", response)
    
    # Check if placing an order for an out of stock item returns an error
    s = socket.socket()
    product = "place_order fox 200"
    s.connect((backend, backendOrderPort3)) 
    s.send(product.encode())
    response = s.recv(1024).decode()
    s.close()
    if('error' in response):
        print("SUCCESS: Order of item with more stock than available:", response)
    else:
        print("FAIL: Order of item with more stock than available issue:", response)


    # Check if placing an order and checking the order log returns the correct order info
    s = socket.socket()
    product = "place_order tux 2"
    s.connect((backend, backendOrderPort3)) 
    s.send(product.encode())
    buy_info = json.loads(s.recv(1024).decode())
    s.close()
    s = socket.socket()
    order_info = "check_order " + str(buy_info['data']['order_number'])
    s.connect((backend, backendOrderPort3)) 
    s.send(order_info.encode())
    order_response = json.loads(s.recv(1024).decode())
    s.close()
    if((not 'error' in order_response) and (order_response['data']['number'] == buy_info['data']['order_number'])):
        if(order_response['data']['name'] == 'tux'  and order_response['data']['quantity'] == 2):
            print("SUCCESS: Orders on check returns correct info")
    else:
        print("ERROR: Orders check returns wrong info")


    # Check if placing an order on one replica shows on the others
    s = socket.socket()
    product = "place_order tux 2"
    s.connect((backend, backendOrderPort3)) 
    s.send(product.encode())
    buy_info = json.loads(s.recv(1024).decode())
    s.close()
    s = socket.socket()
    order_info = "check_order " + str(buy_info['data']['order_number'])
    s.connect((backend, backendOrderPort2)) 
    s.send(order_info.encode())
    order_response2 = json.loads(s.recv(1024).decode())
    s.close()
    s = socket.socket()
    s.connect((backend, backendOrderPort1)) 
    s.send(order_info.encode())
    order_response1 = json.loads(s.recv(1024).decode())
    s.close()
    if((not 'error' in order_response1) and (not 'error' in order_response2 ) and (order_response1['data']['number'] == order_response2['data']['number']) and (order_response2['data']['number'] == buy_info['data']['order_number'])):
        if(order_response2['data']['name'] == 'tux' and order_response1['data']['name'] == 'tux' and order_response1['data']['quantity'] == 2 and order_response2['data']['quantity'] == 2):
            print("SUCCESS: Orders on replica 1 correctly appear on replicas 2 and 3")
    else:
        print("ERROR: Orders on replica do not appear on replicas 2 and 3")

if __name__ == '__main__':
    tests()
