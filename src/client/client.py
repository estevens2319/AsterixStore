import http.client
import json
import random
import os

# This is a function created by ChatGPT for extracting environmental variables from a .env file
def load_env(file_path):
    #Load environmental variables from a .env file.
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except FileNotFoundError:
        print("No .env found, proceeding as normal")
# Load variables from .env file
load_env('../.env')


# Address of the frontend server
frontend_address = os.environ.get('FRONTEND_HTTP_ADDRESS')
if(frontend_address):
    print("Frontend Environmental Address found:", frontend_address)
else:
    frontend_address = 'localhost'
    print("Using default frontend address:", frontend_address)

frontend_HTTP_port = os.environ.get('FRONTEND_HTTP_PORT')
if(frontend_HTTP_port):
    frontend_HTTP_port = int(frontend_HTTP_port)
    print("Frontend HTTP Environmental Port found:", frontend_HTTP_port)
else:
    frontend_HTTP_port = 1234
    print("Using default frontend HTTP port:", frontend_HTTP_port)

# Send a query request to the HTTP server
def query_catalog(product_name, connection):
    # Generation the path with the product name and send the request
    path = "/products/" + product_name.lower()
    connection.request("GET", path)
    # Recieve the request as a json, decode it, and send it
    json_response = json.loads(connection.getresponse().read().decode())
    return json_response

# Send an order request to the HTTP server
def place_order(product_name, quantity, connection):
    # Generate the path and the order info json, and send it to the HTTP server
    path = "/orders"
    order_info = {'name': product_name.lower(), 'quantity': quantity}
    json_order = json.dumps(order_info)
    connection.request("POST", path, json_order)
    # Recieve the json response, doce and return it
    json_response = json.loads(connection.getresponse().read().decode())
    return json_response

# Send a check order request to the HTTP server 
def get_order(order_num, connection):
    # Generation the path with the order number and send the request
    path = "/orders/" + str(order_num)
    connection.request("GET", path)
    # Recieve the request as a json, decode it, and send it
    json_response = json.loads(connection.getresponse().read().decode())
    return json_response

# Automatic interface for interacting with the store
def auto(server_address):
    # Establish the HTTP connection with the server
    connection = http.client.HTTPConnection(server_address)
    toys = ['whale', 'tux', 'fox', 'lego', 'rubiks', 'gameboy', 'atari', 'chess', 'dnd', 'pinball', 'uno']
    p = 0 #random.random()
    quantity = 1
    orders_placed = []
    # while(True):
    for i in range(0, 5):
        # Pick a random toy and query the catalog with it
        currToy = toys[random.randint(0, 2)]
        response = query_catalog(currToy, connection)
        print("Queried:", currToy)
        if(not 'error' in response):
            # If there was no error, print the response from the server
            print("Quantity:", response['data']['quantity'])
            if(int(response['data']['quantity']) > 0):
                # If the item is in stock, randomly place an order for it
                if(random.random() > p):
                    # If the random number was greater than p, place an order for 1 of that product
                    print("Placing order for 1", currToy)
                    order_info = place_order(currToy, quantity, connection)['data']
                    if(not 'error' in order_info):
                        order_info['name'] = currToy
                        order_info['quantity'] = quantity
                        orders_placed.append(order_info)

    # After orders have been placed, check to see if looking up the order number retrieves the correct data
    for order in orders_placed:
        order_reply = get_order(order['order_number'], connection)
        if('error' in order_reply):
            print(order_reply)
        else:
            order_reply = order_reply['data']
            print(order_reply['number'] == order['order_number'], "Reply:", order_reply['number'], "Local:", order['order_number'])
            print(order_reply['name'] == order['name'], "Reply:", order_reply['name'], "Local:", order['name'])
            print(order_reply['quantity'] == order['quantity'], "Reply:", order_reply['quantity'], "Local:", order['quantity'])


# Human interface for interacting with the store
def human(server_address):
    # Establish the HTTP connection with the server
    connection = http.client.HTTPConnection(server_address)
    while(True): 
        choice = input("Q: Query\nB: Buy\nO: Check Order\n")
        # Get human input to buy or query
        if(choice.lower() == "b"):    
            # If its a buy, get the product and quantity and send place the order
            product = input("What product do you want?\n")
            quantity = input("How many?\n")
            print("Attempting to buy")
            print(place_order(product, quantity, connection))
        elif(choice.lower() == "o"):
            # If it is an order check, get the order number and check on it 
            order_num = input("What is the order number to check?\n")
            print("Checking order number")
            print(get_order(order_num, connection))
        else:
            # If its not a buy, query for the product
            product = input("What product do you want?\n")
            print("Querying")
            print(query_catalog(product, connection))


if __name__ == '__main__':
    server_address = frontend_address + ":" + str(frontend_HTTP_port)
    human(server_address)
    # auto(server_address)
