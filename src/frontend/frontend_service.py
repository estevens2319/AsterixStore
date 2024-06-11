from http.server import HTTPServer, BaseHTTPRequestHandler
import socket
import json
import threading
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

# This section involves acquiring environmental variables
# or setting default values for the addresses and ports
######################################################################
catalog_address = os.environ.get('CATALOG_ADDRESS')
if(catalog_address):
    print("Catalog Environmental Address found:", catalog_address)
else:
    catalog_address = 'localhost'
    print("Using default catalog address:", catalog_address)


catalog_port = os.environ.get('CATALOG_PORT')
if(catalog_port):
    catalog_port = int(catalog_port)
    print("Catalog Environmental Port found:", catalog_port)
else:
    catalog_port = 2319
    print("Using default catalog port:", catalog_port)


order_addresses = os.environ.get('ORDER_ADDRESSES')
if(order_addresses):
    order_addresses = order_addresses.split(",")
    print("Order Environmental Addresses found:", order_addresses)
else:
    order_addresses = ['localhost', 'localhost', 'localhost']
    print("Using default order address:", order_addresses)


order_ports = os.environ.get('ORDER_PORTS')
if(order_ports):
    order_ports = order_ports.split(",")
    order_ports = [int(port) for port in order_ports]
    print("Order Environmental Ports found:", order_ports)
else:
    order_ports = [1115, 1116, 1117]
    print("Using default order port:", order_ports)


frontend_address = os.environ.get('FRONTEND_ADDRESS')
if(frontend_address):
    print("Frontend Environmental Address found:", frontend_address)
else:
    frontend_address = 'localhost'
    print("Using default frontend address:", frontend_address)


frontend_HTTP_address = os.environ.get('FRONTEND_HTTP_ADDRESS')
if(frontend_HTTP_address):
    print("Frontend HTTP Environmental Address found:", frontend_HTTP_address)
else:
    frontend_HTTP_address = 'localhost'
    print("Using default frontend HTTP address:", frontend_HTTP_address)


frontend_HTTP_port = os.environ.get('FRONTEND_HTTP_PORT')
if(frontend_HTTP_port):
    frontend_HTTP_port = int(frontend_HTTP_port)
    print("Frontend HTTP Environmental Port found:", frontend_HTTP_port)
else:
    frontend_HTTP_port = 1234
    print("Using default frontend HTTP port:", frontend_HTTP_port)

frontend_TCP_port = os.environ.get('FRONTEND_TCP_PORT')
if(frontend_TCP_port):
    frontend_TCP_port = int(frontend_TCP_port)
    print("Frontend TCP Environmental Port found:", frontend_TCP_port)
else:
    frontend_TCP_port = 6789
    print("Using default frontend TCP port:", frontend_TCP_port)

cache_size = os.environ.get('CACHE_SIZE')
if(cache_size):
    cache_size = int(cache_size)
    print("Environmental cache size found:", cache_size)
else:
    cache_size = 5
    print("Using default cache size:", cache_size)


order_service_ID_list = os.environ.get('ORDER_SERVICE_ID_LIST')
if(order_service_ID_list):
    order_service_ID_list = order_service_ID_list.split(",")
    order_service_ID_list = [int(id) for id in order_service_ID_list]
    print("Order Environmental IDs found:", order_service_ID_list)
else:
    order_service_ID_list = [0, 1, 2]
    print("Using default order IDs:", order_service_ID_list)

order_service_dict = {}
for i in range(0, len(order_service_ID_list)):
    order_service_dict[order_service_ID_list[i]] = {'address':order_addresses[i], 'port':order_ports[i]}
print(order_service_dict)

curr_order_leader = None

leader_lock = threading.Lock()

######################################################################

# Function that alerts all other order_services that a new leader has been selected
def alertLeader(leader_id):
    message = "leader_selection " + str(leader_id)
    # For every order service id in the list, try connecting and sending a message notifying of the new leader.
    # If connection is unsuccessful, print it and move to the next id.
    for order_service_id in order_service_ID_list:
        try:
            s = socket.socket()
            s.connect((order_service_dict[order_service_id]['address'], order_service_dict[order_service_id]['port'])) 
            s.send(message.encode())
            s.close()
        except ConnectionRefusedError:
            print("Tried to alert Service ID of leader but", order_service_id, "is down.")
        except ConnectionResetError:
            print("Tried to alert Service ID of leader but", order_service_id, "is down.")

# Algorithm for choosing a new leader from the available order service IDs
def chooseLeader():
    print("choosing leader")
    message = "check_health"
    # First, sort the order service IDs so that we try selecting the highest value ID first then move down until we find one that is healthy
    order_service_ID_list.sort(reverse=True)
    # For every order service ID try to connect and send a health check. As soon as we get a reply (since it is sorted) we elect that ID as the leader
    # If the connection does not work, we continue to the next ID in the list.
    # If no IDs are found to be healthy we return None
    for order_service_id in order_service_ID_list:
        try:
            s = socket.socket()
            s.connect((order_service_dict[order_service_id]['address'], order_service_dict[order_service_id]['port'])) 
            s.send(message.encode())
            backend_reply = s.recv(1024).decode()
            print(backend_reply)
            s.close()
            alertLeader(order_service_id)
            return order_service_id
        except ConnectionRefusedError:
            print("Service ID", order_service_id, "is down.")
        except ConnectionResetError:
            print("Tried to alert Service ID of leader but", order_service_id, "is down.")
    return None


# Class for the frontends cache
class Cache:
    def __init__(self, size):
        # Initialize the dictionary used to store the toy/quantity in the cache
        # Initialize the list holding the last {size} used toys in the cache
        self.cache = {}
        self.recents = []
        self.size = size
        for i in range(0, self.size):
            self.recents.append(None)

    def get(self, toy):
        # If the toy exists in the cache, remove it from the recently used list and move it to
        # the front of the list since it was the most recently used
        if(toy in self.cache):
            self.recents.remove(toy)
            self.recents.insert(0, toy)
            return self.cache[toy]
        return None

    # Set a toy in the cache
    # If the toy already exists in the cache, remove it from its position and move it to the front
    # since it is now the most recently used toy in the cache
    # If it does not exist in the cache already, remove the last element in the cache 
    # and insert the new toy in the front of the cache   
    def set(self, toy, price, quantity):
        if toy in self.recents:
            self.recents.remove(toy)
            self.recents.insert(0, toy)
            self.cache[toy] = {'quantity': str(quantity), 'price': str(price)}
        else:    
            self.cache.pop(self.recents[self.size-1], None)
            self.recents.insert(0, toy)
            self.recents.pop()
            self.cache[toy] = {'quantity': str(quantity), 'price': str(price)}
    
    # Remove a toy from the list and add None to the back of the list 
    # To mantain a cache size of 5
    def remove(self, toy):
        if(toy == None):
            return
        if toy in self.recents:
            self.recents.remove(toy)
            self.recents.insert(self.size-1, None)
            self.cache.pop(toy)

    # Print the cache for debugging
    def printthings(self):
        print("Cache:\n", self.cache)
        print("Recents:\n", self.recents)




class ServerRequestHandler(BaseHTTPRequestHandler):
    
    # Perform a GET HTTP request
    def do_GET(self):
        # Attach headers to the HTTP response
        global curr_order_leader
        self.send_response(200)
        self.end_headers()
        paths = self.path.split('/')
        # Read the path
        if(paths[1] == "products"):
            # If the path is correct, get the toy from the path
            toy = str(paths[len(paths) - 1])
            # Check if the cache has the toy and if so, return that instead of querying the catalog
            cached_toy = frontend_cache.get(toy)
            if(cached_toy != None):
                reply = {'data' : {'name': toy, 'price': cached_toy['price'], 'quantity': cached_toy['quantity']}}
                json_data = json.dumps(reply)
                self.wfile.write(json_data.encode())
            # If the cache doesnt have the toy, send the request to the catalog
            else:
                product = "query " + toy
                # Create a socket connection with the backend catalog and send the request
                s = socket.socket()
                s.connect((catalog_address, catalog_port)) 
                s.send(product.encode())
                backend_reply = s.recv(1024)
                s.close()
                # Cache the reply from the catalog
                json_reply = json.loads(backend_reply)
                if(not 'error' in json_reply):
                    frontend_cache.set(json_reply['data']['name'], json_reply['data']['price'], json_reply['data']['quantity'])
                # Send the reply from the catalog to the client
                self.wfile.write(backend_reply)

        # If the request is for checking orders:
        elif(paths[1] == "orders"):
            message = "check_order " + str(paths[len(paths) - 1])
            # Create a connection with the order service and send a message with the order number to check
            connecting = True
            backend_reply = None
            # Keep attempting to connect to the order service until it is reached
            while(connecting):
                # Try connecting to the leader order service
                try:
                    s = socket.socket()    
                    s.connect((order_service_dict[curr_order_leader]['address'], order_service_dict[curr_order_leader]['port'])) 
                    s.send(message.encode())
                    backend_reply = (s.recv(1024))
                    s.close()
                    connecting = False

                # If connecting to the leader service FAILS, hide it from the client and attempt to choose a new leader
                # If the leader lock is locked, then another thread has already begun the new leader selection process. 
                # If the connection failed and the leader lock is not in use, then start the new leader selection.
                # Continue the new leader selection until a leader is found, the client will never see an error.

                except KeyError:                    
                    # If the curr order leader is equal to None(chooseleader process is ongoing)
                    if not leader_lock.locked():
                        with leader_lock:
                            print("Service ID", curr_order_leader, "is down.")
                            curr_order_leader = None
                            while(curr_order_leader == None):
                                curr_order_leader = chooseLeader()
                except ConnectionRefusedError:
                    # If the curr order leader is not running 
                    if not leader_lock.locked():
                        with leader_lock:
                            print("Service ID", curr_order_leader, "is down.")
                            curr_order_leader = None
                            while(curr_order_leader == None):
                                curr_order_leader = chooseLeader()
                except ConnectionResetError:
                    # If the curr order leader crashed mid connection
                    if not leader_lock.locked():
                        with leader_lock:
                            print("Service ID", curr_order_leader, "is down.")
                            curr_order_leader = None
                            while(curr_order_leader == None):
                                curr_order_leader = chooseLeader()
            # Take the reply from the order service and send it to the client.
            self.wfile.write(backend_reply)
        else:
            # If the path isnt for products or orders, create the error json and reply with it
            reply = {'error': {'code' : 202, 'message': "Incorrect Path"}}
            json_data = json.dumps(reply)
            self.wfile.write(json_data.encode())
        # frontend_cache.printthings()

    # Perform a POST HTTP request
    def do_POST(self):
        global curr_order_leader
        # Attach headers the the HTTP resonse
        self.send_response(200)
        self.end_headers()
        # Read the path
        paths = self.path.split('/')
        if(paths[1] != "orders"):
            # If the path isnt for orders, create the error json and reply with it
            reply = {'error': {'code' : 202, 'message': "Incorrect Path"}}
            json_data = json.dumps(reply)
            self.wfile.write(json_data.encode())
        else:
            # If the path is correct, extract the information from the request to create the order json to send to the order service
            content_length = int(self.headers['Content-Length'])
            json_order = self.rfile.read(content_length)
            order_info = json.loads(json_order.decode())
            message = "place_order " + order_info['name'] +" "+ str(order_info['quantity'])
            # Create a connection with the order service and send the order json with the order info
            connecting = True
            backend_reply = None
            # keep attempting to connect to order service until it is reached, dont show an error to the client
            while(connecting):
                try:
                    s = socket.socket()    
                    s.connect((order_service_dict[curr_order_leader]['address'], order_service_dict[curr_order_leader]['port'])) 
                    s.send(message.encode())
                    backend_reply = (s.recv(1024))
                    s.close()
                    connecting = False
                
                # If connecting to the leader service FAILS, hide it from the client and attempt to choose a new leader
                # If the leader lock is locked, then another thread has already begun the new leader selection process. 
                # If the connection failed and the leader lock is not in use, then start the new leader selection.
                # Continue the new leader selection until a leader is found, the client will never see an error.

                except KeyError:
                    # if the curr order leader is None (chooseleader process is ongoing)
                    if not leader_lock.locked():
                        with leader_lock:
                            print("Service ID", curr_order_leader, "is down.")
                            curr_order_leader = None
                            while(curr_order_leader == None):
                                curr_order_leader = chooseLeader()
                except ConnectionRefusedError:
                    # If the curr order leader is not running 
                    if not leader_lock.locked():
                        with leader_lock:
                            print("Service ID", curr_order_leader, "is down.")
                            curr_order_leader = None
                            while(curr_order_leader == None):
                                curr_order_leader = chooseLeader()
                except ConnectionResetError:
                    # If the curr order leader crashed mid connection
                    if not leader_lock.locked():
                        with leader_lock:
                            print("Service ID", curr_order_leader, "is down.")
                            curr_order_leader = None
                            while(curr_order_leader == None):
                                curr_order_leader = chooseLeader()
            # Take the reply from the order service and send it to the client.
            self.wfile.write(backend_reply)

# Modifications the the base HTTPServer class that has it run with a new thread for each http session
class FrontEndServer(HTTPServer):
    def process_request(self, request, adress):
        # When a new HTTP connection request is recieved, create a new thread to handle that connection
        t = threading.Thread(target=self.new_thread, args=(request, adress))
        t.start()
    # Function for each thread to run, tells the thread to handle all requests from the connection it is bound to
    def new_thread(self, request, adress):
        self.RequestHandlerClass(request, adress, self)

# Function that the http server thread runs, initializing the HTTPserver
def startHTTPServer():
    server = FrontEndServer((frontend_HTTP_address, frontend_HTTP_port), ServerRequestHandler)
    print("Starting Front End Server")
    # Server the server forever
    server.serve_forever()

# Function that handles the catalog sending an invalidation message
def catalog_invalidate(connection):
        # Keep the connection open until the client closes it
        while True:
            # Recieve the incoming request and if empty, quit the loop and close the connection
            data = connection.recv(1024)
            if not data:
                break
            request = data.decode().split(" ")
            # For every toy in the invalidation request, remove it from the cache
            if(request[0] == "invalidate"):
                request.pop(0)
                for toy in request:
                    frontend_cache.remove(toy)
        connection.close()

# Function to start a TCP server to recieve invalidation messages from the catalog service
def startTCPServer(address, port):
    print("Starting tcp server for catalog invalidations")
    s = socket.socket()
    s.bind((address, port))
    s.listen(5)
    print("socket is listening")
    # Serve the server until the code is exited
    while True:
        c, addr = s.accept()
        print("Connection from:", addr[0], ":", addr[1])
        # For each new connection, create a new thread to handle it
        t = threading.Thread(target=catalog_invalidate, args=(c,))
        t.start()




def main():
    # Create the server on the frontend address and port

    # Initialize the global cache 
    global frontend_cache
    frontend_cache = Cache(cache_size)  
    # Select the first order service leader
    global curr_order_leader
    while(curr_order_leader == None):
        curr_order_leader = chooseLeader()

    # Create one server to listen to HTTP requests
    httpThread = threading.Thread(target=startHTTPServer)
    httpThread.start()
    # Create one server to lsiten to TCP requests from the catalog service about cache updates 
    tcpThread = threading.Thread(target=startTCPServer, args=(frontend_address, frontend_TCP_port))
    tcpThread.start()

        

    
if __name__ == "__main__":
    main()