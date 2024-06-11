import http.client
import json
import random
import os
import time
import threading

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

# implement a wait lock so after the clients finish running and start to create the dictionary 
# used for the average times, they dont all overwrite at once
wait_lock =threading.Lock()
wait_times = {}
iterations = 10
# Automatic interface for interacting with the store
def auto(server_address, clientID, p):
    # Establish the HTTP connection with the server
    global iterations
    connection = http.client.HTTPConnection(server_address)
    toys = ['whale', 'tux', 'fox', 'lego', 'rubiks', 'gameboy', 'atari', 'chess', 'dnd', 'pinball', 'uno']
    global wait_times
    quantity = 1
    orders_placed = []
    query_response_times = []
    buy_response_times = []
    order_check_response_times = []
    # while(True):

    # Repeats {iteration} times. takes the time difference from before and after each HTTP request
    # Saves them to a list and adds them to a global dictionary for averaging later.
    for i in range(0, iterations):
        # Pick a random toy and query the catalog with it
        currToy = toys[random.randint(0, 2)]
        pre_query = time.time()
        response = query_catalog(currToy, connection)
        query_response_times.append(((time.time() - pre_query) * 1000))
        if(not 'error' in response):
            # If there was no error, print the response from the server
            # print("Quantity:", response['data']['quantity'])
            if(int(response['data']['quantity']) > 0):
                # If the item is in stock, randomly place an order for it
                if(random.random() > p):
                    # If the random number was greater than p, place an order for 1 of that product
                    pre_buy = time.time()
                    order_info = place_order(currToy, quantity, connection)
                    buy_response_times.append(((time.time() - pre_buy) * 1000))
                    if(not 'error' in order_info):
                        order_info['data']['name'] = currToy
                        order_info['data']['quantity'] = quantity
                        orders_placed.append(order_info)
                    else:
                        print(order_info)

    # Check the order number for each order successfully placed
    for order in orders_placed:
        if(not 'error' in order):
            pre_check = time.time()
            order_reply = get_order(order['data']['order_number'], connection)
            order_check_response_times.append(((time.time() - pre_check) * 1000))
    with wait_lock:
        wait_times[clientID] = {'query': query_response_times, 'buy':buy_response_times, 'check':order_check_response_times}


if __name__ == '__main__':
    server_address = frontend_address + ":" + str(frontend_HTTP_port)
    clients  = []
    p = 0
    # Create 5 clients
    for i in range(0, 5):
        clients.append(threading.Thread(target=auto, args=(server_address, i, p)))
    start_time = time.time()
    for client in clients:
        client.start()
    for client in clients:
        client.join()
    # Start the clients and wait for them to finish running
    # Calculate the total and average times for different types of actions
    total_time = (time.time() - start_time) * 1000
    all_queries = []
    all_buys = []
    all_checks = []
    for i in range(0, 5):
        all_queries += wait_times[i]['query']
        all_buys += wait_times[i]['buy']
        all_checks +=  wait_times[i]['check']
    avg_queries = sum(all_queries) / len(all_queries)
    avg_buys = sum(all_buys) / len(all_buys)
    avg_checks =  sum(all_checks) / len(all_checks)
    print("With P =", p, "And running", iterations, "iterations")
    print("Total time:", total_time)
    print("Average Query time:", avg_queries)
    print("Average Buy Time:", avg_buys)
    print("Average Check Time:", avg_checks)
