import http.client
import json
import random

server_address = "localhost:1234"

def query_catalog(product_name, connection):
    path = "/products/" + product_name.lower()
    connection.request("GET", path)
    json_response = json.loads(connection.getresponse().read().decode())
    return json_response

def place_order(product_name, quantity, connection):
    path = "/orders"
    order_info = {'name': product_name.lower(), 'quantity': quantity}
    json_order = json.dumps(order_info)
    connection.request("POST", path, json_order)
    json_response = json.loads(connection.getresponse().read().decode())
    return json_response

def test():
    connection = http.client.HTTPConnection(server_address)
    toys = ['whale', 'tux', 'fox']

    # Check if a normal query works
    response = query_catalog('tux', connection)
    if('name' in response['data'] and 'quantity' in response['data'] and 'price' in response['data']):
        print("SUCCESS: Normal Query works:", response)
    else:
        print("FAIL: Normal query issue:", response)

    # Check if a query for a non existant item returns an error
    response = query_catalog('CS677', connection)
    if('error' in response):
        print("SUCCESS: Query for non existant item worked:", response)
    else:
        print("FAIL: Non existant item issue:", response)

    # Chech if placing an order for an in stock item works
    response = place_order('tux', 1, connection)
    if(not 'error' in response):
        print("SUCCESS: Order for in stock item worked:", response)
    else:
        print("FAIL: Order for in stock item issue:", response)

    # Check if placing an order for an out of stock item returns an error
    response = place_order('fox', 200, connection)
    if('error' in response):
        print("SUCCESS: Order of item with more stock than available:", response)
    else:
        print("FAIL: Order of item with more stock than available issue:", response)
    
    # Check if placing an order for a non existant item returns an error
    response = place_order('CS677', 1, connection)
    if('error' in response):
        print("SUCCESS: Order for non existant item worked:", response)
    else:
        print("FAIL: Order for non existant item issue:", response)


    # Check if killing a replica successfully adds a new leader
    response = place_order('tux', 2, connection)
    if(not 'error' in response):
        print("SUCCESS Part 1: Order for in stock item worked. Continue to kill replica:", response)
        cont = input("Kill the leader order service to continue this test case. Enter Y when done.")
        while(cont.lower() != "y"):
            cont = input("Kill the leader order service to continue this test case. Enter Y when done.")
        response = place_order('tux', 2, connection)
        if(not 'error' in response):
            print("SUCCESS Part 2: Order for in stock item after killing leader order service worked:", response)
        else:
            print("FAIL: Issue after killing leader order servidce:", response)
    else:
        print("FAIL: Order for in stock item issue:", response)

if __name__ == '__main__':
    test()