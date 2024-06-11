import socket
import threading
import json
import time
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

frontend_address = os.environ.get('FRONTEND_ADDRESS')
if(frontend_address):
    print("Frontend Environmental Address found:", frontend_address)
else:
    frontend_address = 'localhost'
    print("Using default frontend address:", frontend_address)

frontend_TCP_port = os.environ.get('FRONTEND_TCP_PORT')
if(frontend_TCP_port):
    frontend_TCP_port = int(frontend_TCP_port)
    print("Frontend TCP Environmental Port found:", frontend_TCP_port)
else:
    frontend_TCP_port = 6789
    print("Using default frontend TCP port:", frontend_TCP_port)
######################################################################

# Class that handles the database
class Database():
    
    def __init__(self):    
        # Open the database file on the machine
        database_file = open('database.txt', 'r')
        file_content = database_file.read().split('\n')
        database_file.close()
        self.database = {}
        for line in file_content:
            if(len(line) != 0):
                split_line = line.split(" ")
                self.database[split_line[0]] = {'price':split_line[1], 'quantity':split_line[2]}
            # Initialize the database with the data from the database file
        self.requests_since_last_write = 0
        self.db_request_cap = 1 # Set how often the database is written to the file
        self.db_lock = threading.Lock()

    # Function that will write the current working database to the local machines database file
    def write_to_file(self):
        db_file_contents = ""
        # Build the string to write to the database file
        for line in self.database:
            db_file_contents += line + " " + self.database[line]['price'] + " " + self.database[line]['quantity'] + '\n'
        db_file = open('database.txt', 'w')
        db_file.write(db_file_contents[:-1]) # write to the database file. 
        db_file.close()
        self.requests_since_last_write = 0
    
    # Perform a query look up on the database
    def query(self, product):
        # If the product exists in our database return it, otherwise return none.
        if(product in self.database):
            return self.database[product]
        return None
    
    # Function to check stock and restock to 100 items that need restocking
    def restock(self):
        restocked_toys = ""
        with self.db_lock:
            for toy in self.database:
                # Check every toy in the database and if it is empty, restock it to 100
                if(int(self.database[toy]['quantity']) <= 0):
                    self.database[toy]['quantity'] = '100'
                    restocked_toys += toy + " "
            # Write restocked database to the disk file
            self.write_to_file()        
        if(len(restocked_toys) != 0):
            restocked_toys = restocked_toys[:-1]
            # If we restocked items, remove the trailing white space at the end
        return restocked_toys
    
    # Carry out an order in the database
    def order(self, product, quantity):
        # If the product exists
        if(product in self.database):
            with self.db_lock: # Aquire the database lock since we are accessing quantity information
                if(int(self.database[product]['quantity']) < int(quantity)):
                    return -2 # If there is not enough quantity to fulfil order, return error code -2
                else:
                    # If the order is successful, decrease the quantity in the database
                    self.database[product]['quantity'] = str(int(self.database[product]['quantity']) - int(quantity))
                    self.requests_since_last_write += 1
                    if(self.requests_since_last_write >= self.db_request_cap):
                        # Increment the orders since last write to file counter and if necessary write the database to the file
                        self.write_to_file()
                    return 1 # The order has bee successfully completed and we return the success code
        else:
            return -1 # If the product doesnt exist in the database return error code -1
        
class Catalog_Service:

    def __init__(self, address, port):
        # Initialize the database and start the server listening on a new thread and start a new thread to handle the restock timer
        self.database = Database()
        self.restock_timer = threading.Thread(target = self.timer)
        self.catalog_server = threading.Thread(target=self.start_server, args=(address, port,))
        self.catalog_server.start()
        self.restock_timer.start()
    
    def start_server(self, address, port):
        # Start the server listening on a socket connection on the given address and port
        self.s = socket.socket()
        self.s.bind((address, port))
        print("Catalog socket binded to port", port)
        self.s.listen(5)
        print("socket is listening")
        # Serve the server until the code is exited
        while True:
            c, addr = self.s.accept()
            print("Connection from:", addr[0], ":", addr[1])
            # For each new connection, create a new thread to handle it
            t = threading.Thread(target=self.handle_request, args=(c,))
            t.start()

    # Function that sends an invalidation request to the frontend's cache
    # This function is called whenever an order or a restock takes place
    def sendInvalidate(self, toys):
        print("sending invalidation")
        invalidate = "invalidate " + toys
        s = socket.socket()
        s.connect((frontend_address, frontend_TCP_port)) 
        s.send(invalidate.encode())
        s.close()
        # Create a tcp connection with the front end and send a message containing all the toys that need to be invalidated

    # Function that keeps track of time and attempts a restock every 10 seconds
    # Every 10 seconds it will tell the database to restock and then call the sendInvalidate function along with the list of toys to invalidate
    def timer(self):
        currTime = time.time()
        while(True):
            if(time.time() - currTime > 10):
                print("Checking stock")
                restocked_toys = self.database.restock()
                if(len(restocked_toys) != 0):
                    self.sendInvalidate(restocked_toys)
                currTime = time.time()

    # Handle incoming requests
    def handle_request(self, connection):
        # Keep the connection open until the client closes it
        while True:
            # Recieve the incoming request and if empty, quit the loop and close the connection
            data = connection.recv(1024)
            if not data:
                break
            # Decode and split the request
            request = data.decode().split(" ")
            # If the request is an order request perform the database order function and reply
            if(request[0] == "order"):
                reply = str(self.database.order(request[1], request[2]))
                if(reply == "1"):
                    self.sendInvalidate(request[1])
                # If the order went through successfully, send an invalidation to the front end for that toy
                connection.sendall(reply.encode())
            # If the request is a query request perform the query function and reply
            elif(request[0] == "query"):
                product = request[1]
                catalog_data = self.database.query(product)
                # If the item is not found reply with an error
                if(catalog_data == None):
                    reply = {'error': {'code' : 404, 'message': "Item not found."}}
                    json_data = json.dumps(reply)
                    connection.sendall(json_data.encode())
                # If the product is found, create the json response and reply with it
                else:
                    reply = {'data' : {'name': product, 'price': catalog_data['price'], 'quantity': catalog_data['quantity']}}
                    json_data = json.dumps(reply)
                    connection.sendall(json_data.encode())
            # If the request is neither a query or an order, return an error
            else:
                reply = {'error': {'code' : 101, 'message': "Function type not recognized."}}
                json_data = json.dumps(reply)
                connection.sendall(json_data.encode())
        connection.close()

def main():
    # Start the catalog service
    catalog = Catalog_Service(catalog_address, catalog_port)
    catalog.catalog_server.join()

if __name__ == "__main__":
    main()