import socket
import threading
import json
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

order_addresses_list = os.environ.get('ORDER_ADDRESSES')
if(order_addresses_list):
    order_addresses_list = order_addresses_list.split(",")
    print("Order Environmental Addresses found:", order_addresses_list)
else:
    order_addresses_list = ['localhost', 'localhost', 'localhost']
    print("Using default order address:", order_addresses_list)

order_ports_list = os.environ.get('ORDER_PORTS')
if(order_ports_list):
    order_ports_list = order_ports_list.split(",")
    order_ports_list = [int(port) for port in order_ports_list]
    print("Order Environmental Ports found:", order_ports_list)
else:
    order_ports_list = [1115, 1116, 1117]
    print("Using default order port:", order_ports_list)

order_service_ID_list = os.environ.get('ORDER_SERVICE_ID_LIST')
if(order_service_ID_list):
    order_service_ID_list = order_service_ID_list.split(",")
    order_service_ID_list = [int(id) for id in order_service_ID_list]
    print("Order Environmental IDs found:", order_service_ID_list)
else:
    order_service_ID_list = [0, 1, 2]
    print("Using default order IDs:", order_service_ID_list)

order_ID_position = os.environ.get('ORDER_SERVICE_ID')
if(order_ID_position):
    order_ID_position = int(order_ID_position)
    print("Order service ID position environment found:", order_ID_position)
else:
    order_ID_position = 2
    print("Using default order service ID position:", order_ID_position)

order_service_dict = {}
for i in range(0, len(order_service_ID_list)):
    order_service_dict[order_service_ID_list[i]] = {'address':order_addresses_list[i], 'port':order_ports_list[i]}

# Current ID of this order service iteration
order_service_id = order_service_ID_list[order_ID_position]
order_address = order_addresses_list[order_ID_position]
order_port = order_ports_list[order_ID_position]
leader_id = None
######################################################################

# Order service server class
class Order_Service:

    def __init__(self, address, port):
        # Initialize the order server in a new thread
        self.order_thread = threading.Thread(target=self.start_server, args=(address, port,))
        log_path = "orderlogs" + str(order_ID_position) + ".txt"
        log = open(log_path, 'r')
        # Open the order logs for this order service ID and read it to find the next order number
        log_lines = log.read().split("\n")
        self.log_dict = {}
        last_line = log_lines[len(log_lines)-1]
        if(len(last_line) == 0):
            # If the order log is empty, start the order number at 0
            self.current_order_number = 0
        else:
            # If there are orders in the log, pick up the order number at the previous number plus 1
            for order in log_lines:
                num, name, quan =  order.split(" ")
                self.log_dict[int(num)] = [name, quan]
            self.current_order_number = int(last_line.split(" ")[0]) + 1
        log.close()
        # Create a lock for accessing the order log file
        self.log_lock = threading.Lock()
        # Before starting the server, ask the other running servers for missed orders to add to this log
        with(self.log_lock):
            self.request_missing_logs(self.current_order_number)
        # Start the server
        self.order_thread.start()
        

    # Function that serves the order service
    def start_server(self, address, port):
        # Create a socket server on the specified port and address
        self.s = socket.socket()
        self.s.bind((address, port))
        print("Order socket binded to port", port)
        self.s.listen(5)
        print("socket is listening")
        # Keep the server up until terminated 
        while True:
            c, addr = self.s.accept()
            print("Connection from:", addr[0], ":", addr[1])
            # Recieve orders and create a new thread for each new order
            t = threading.Thread(target=self.get_frontend, args=(c,))
            t.start()

    # Add the order to the order log
    def log_order(self, product, quantity):
        # Use the log lock so other threads arent overwriting as other threads are writing
        # with self.log_lock:
        log = None
        # Only write to this order service IDs order log
        log_path = "orderlogs" + str(order_ID_position) + ".txt"
        if(self.current_order_number == 0):
            log = open(log_path, 'w')
            log.write(str(self.current_order_number) + " " + str(product) + " " + str(quantity))
            log.close()
        else: 
            log = open(log_path, 'a') 
            log.write('\n' + str(self.current_order_number) + " " + str(product) + " " + str(quantity))
            log.close()
        self.log_dict[self.current_order_number] = [str(product), str(quantity)]
        self.current_order_number += 1
            # increment the order number for the next order
    
    # Function to place an order 
    def place_order(self, request, connection):
        # Recieve the request and create a connection with the catalog
        s = socket.socket()    
        s.connect((catalog_address, catalog_port))
        message = "order " + str(request[1]) + " " + str(request[2])
        s.send(message.encode())
        catalog_reply = (s.recv(1024).decode())
        s.close()
        # Send the order to the catalog and recieve the reply
        order_success = int(catalog_reply)
        if(order_success == 1):
            # If the order was successful, create the json reply with the order number and send it back to the client
            with self.log_lock:
                reply = {'data' : {'order_number': self.current_order_number}}
                json_data = json.dumps(reply)
                connection.sendall(json_data.encode())
                # After replying to the frontend log the order on this replica and notify other replicas of the order
                self.log_order(request[1], request[2])
                self.send_log_update(request[1], request[2])

        elif(order_success == -1):
            # If the order was not successful, error code -1 means the item was not found. Generate an error json and return it
            reply = {'error': {'code' : 404, 'message': "Item not found."}}
            json_data = json.dumps(reply)
            connection.sendall(json_data.encode())
        elif(order_success == -2):
            # If the order was not successful, error code -2 means there was not enough stock to complete the order. 
            # Generate the error json and return it
            reply = {'error': {'code' : 303, 'message': "Not enough stock to complete order"}}
            json_data = json.dumps(reply)
            connection.sendall(json_data.encode())

    # Function for replying to order number checks
    def check_order(self, request, connection):
        order_num = int(request[1])
        # If we have the order number in the order log, create the json reply and reply with it to the front end
        if(order_num in self.log_dict):
            reply = {'data' : {'number': order_num, 'name': self.log_dict[order_num][0], 'quantity':int(self.log_dict[order_num][1])}}
            json_data = json.dumps(reply)
            connection.sendall(json_data.encode())
        # If the order number doesnt exist in the order log, send an error.
        else:
            reply = {'error': {'code' : 505, 'message': "Order number not found."}}
            json_data = json.dumps(reply)
            connection.sendall(json_data.encode())

    # Function for replying to the health check from the front end
    def check_health(self, connection):
        reply = str(order_service_id) + " is healthy!"
        connection.sendall(reply.encode())

    # Function for notifying other replicas that we have made an order so they can update their own order logs accordingly
    def send_log_update(self, product, quantity):
        message = "log_update " + str(product) + " " + str(quantity)
        for i in range(0, 3):
            # For every replica ID that isnt this current order service's replica ID
            # Send the log update message with the product and the quantity
            if(i != order_ID_position):
                try:
                    s = socket.socket()    
                    s.connect((order_addresses_list[i], order_ports_list[i])) 
                    s.send(message.encode())
                    s.close()
                except ConnectionRefusedError:
                    # If a replica is not responding, ignore it
                    pass

    # Function for recieving an update when another replica has placed an order and this one needs to also log that order
    def recieve_log_update(self, request):
        with self.log_lock:
            self.log_order(request[1], request[2])
        print("updating log")
    
    # Function for replying to a request for missing logs when another order service replica starts so that it is up to date with other replicas
    def send_missing_logs(self, connection, last_order_num):
        message = ""
        with self.log_lock:
            # Open our order service IDs order log
            log_path = "orderlogs" + str(order_ID_position) + ".txt"
            log = open(log_path, 'r')
            log_lines = log.read().split("\n")
            last_line = log_lines[len(log_lines)-1]
            # If our log isnt empty, begin building a message containing all the logs starting at the last order number the requesting replica has 
            if(len(last_line) != 0):        
                for i in range(last_order_num, len(log_lines)):
                    num, name, quantity = log_lines[i].split(" ")
                    message += str(name) + " " + str(quantity) + '\n'
                message = message[:-1]
            if(message == ""):
                message = "no_logs"
            # If this replica has no new logs for the replica requesting them, reply with no_logs, otherwise send the constructed string of logs
            connection.sendall(message.encode())
        print("sending missing logs")

    # Function to request missing logs from other replicas on startup 
    def request_missing_logs(self, last_order_num):
        print("Requesting missing logs")
        message = "missing_logs " + str(last_order_num)
        # construct a message requesting missing logs and include the last known order number for this replica
        missing_logs = ""
        for i in range(0, 3):
            # For every replica ID that is not this repliacas ID, send a request for the order logs
            if(i != order_ID_position):
                try:
                    s = socket.socket()    
                    s.connect((order_addresses_list[i], order_ports_list[i])) 
                    s.send(message.encode())
                    missing_logs = s.recv(1024).decode()
                    s.close()
                except ConnectionRefusedError:
                    # If a connection is refused, that replica is not running, just continue
                    pass
        # If we successfully connected to a replica and the replicas did not reply with no logs, start logging all the logs recieved
        if(missing_logs != "no_logs" and missing_logs != ""):
            lines = missing_logs.split('\n')
            for log in lines:
                product, quantity = log.split(" ")
                self.log_order(product, quantity)

    # Function that handles connections from the front end and performs the correct function based on the request
    def get_frontend(self, connection):
        # Keep the connection open until the client closes it
        global leader_id
        while True:
            data = connection.recv(1024)
            # If the client sends no more data end the loop and close the connection
            if not data:
                break
            request = data.decode().split(" ")
            # If the request is a check order request call the check order function
            if(request[0] == "check_order"):
                self.check_order(request, connection)
            # if the request is a place order request call the place order function
            elif(request[0] == "place_order"):
                self.place_order(request, connection)
            # if the request is a check health request call the check health function
            elif(request[0] == "check_health"):
                self.check_health(connection)
            # if the request is a leader selection request, set the new leader ID
            elif(request[0] == "leader_selection"):
                print("New leader id:", request[1])
                leader_id = request[1]
            # if the request is a log update request THIS IS FROM ANOTHER order service replica
            # perform the log update request 
            elif(request[0] == "log_update"):
                self.recieve_log_update(request)
            # If the request is a missing logs request THIS IS FROM ANOTHER order service replica
            # call the send missing logs function
            elif(request[0] == "missing_logs"):
                self.send_missing_logs(connection, int(request[1]))
        connection.close()

def main():
    # Start the server
    order = Order_Service(order_address, order_port)
    order.order_thread.join()

if __name__ == "__main__":
    main()