import socket
import json

def tests():

    # Test if a query for a normal item works
    backend = 'localhost'
    backendCatalogPort = 2319
    product = "query " + "tux"
    s = socket.socket()
    s.connect((backend, backendCatalogPort)) 
    s.send(product.encode())
    response = json.loads(s.recv(1024))
    s.close()
    if('name' in response['data'] and 'quantity' in response['data'] and 'price' in response['data']):
        print("SUCCESS: Normal Query works:", response)
    else:
        print("FAIL: Normal query issue:", response)

    # Test if a query for a non existant item returns an error
    s = socket.socket()
    product = "query " + "CS677"
    s.connect((backend, backendCatalogPort)) 
    s.send(product.encode())
    response = json.loads(s.recv(1024))
    if('error' in response):
        print("SUCCESS: Query for non existant item worked:", response)
    else:
        print("FAIL: Non existant item issue:", response)
    
    # Test if the wrong function returns an error
    s = socket.socket()
    product = "dontquery " + "tux"
    s.connect((backend, backendCatalogPort)) 
    s.send(product.encode())
    response = json.loads(s.recv(1024))
    if('error' in response):
        print("SUCCESS: Query with wrong function worked:", response)
    else:
        print("FAIL: Query with wrong function issue:", response)

    # Test if an order for an in stock item works
    s = socket.socket()
    product = "order " + "tux 2"
    s.connect((backend, backendCatalogPort)) 
    s.send(product.encode())
    response = s.recv(1024).decode()
    s.close()
    if(response == '1'):
        print("SUCCESS: Normal order works:", response)
    else:
        print("FAIL: Normal order issue:", response)
    
    # Test if an order for a non existant item returns an error
    s = socket.socket()
    product = "order " + "CS677 2"
    s.connect((backend, backendCatalogPort)) 
    s.send(product.encode())
    response = s.recv(1024).decode()
    s.close()
    if(response == '-1'):
        print("SUCCESS: Non existant item order works:", response)
    else:
        print("FAIL: Non existant item order issue:", response)
    
    # Test if an order for an out of stock item returns an error
    s = socket.socket()
    product = "order " + "fox 200"
    s.connect((backend, backendCatalogPort)) 
    s.send(product.encode())
    response = s.recv(1024).decode()
    s.close()
    if(response == '-2'):
        print("SUCCESS: Order of item with more stock than available:", response)
    else:
        print("FAIL: Order of item with more stock than available issue:", response)

if __name__ == '__main__':
    tests()
