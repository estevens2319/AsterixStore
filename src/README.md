## Instructions to run the code 

There are no outside libraries needed to be installed for this code to run.  
Environmental variables for controlling port numbers, addresses, and order service IDs can be found in the .env file.  
If environmental variables are not set, they will be set to their default values in each service.   

## Running the services  
The .env file contains default environmental variables for running the services. Leaving these all as their default is sufficient to run everything locally, the only variable that must be set is ORDER_SERVICE_ID. It is important to set the ORDER_SERVICE_ID to be a different number BEFORE starting each replica, if this is not set, then when a second replica is started, it will attempt to start a server on the address and port already in use which will cause the replica to not start. If this happens, simply set the ORDER_SERVICE_ID environmental variable to something that hasn't been used (0, 1, 2) and run the replica again.  
After setting preferred environmental variables, simply navigate to each individual microservice in a terminal and run:  
python3 frontend_service.py  
python3 order_service.py  
python3 catalog_service.py  
python3 client.py  
python3 load_test_client.py  

## Understanding the environmental variables  
CATALOG_ADDRESS = the address of the catalog that the frontend and order services will connect to using TCP  
FRONTEND_ADDRESS =  the address of the frontend that the catalog and order services will connect to over TCP   
FRONTEND_HTTP_ADDRESS = the address that frontend HTTP service will be hosted from and where the client will connect to.   
ORDER_ADDRESSES = This is the list of addresses where the 3 replicas of the order service are hosted  
CATALOG_PORT = This is the port that the catalog service listens on, frontend and order services will connect to this port.    
ORDER_PORTS = This is the list of ports that the 3 replicas of the order service will be listening on  
ORDER_SERVICE_ID_LIST = This is the list of order service IDs, each order service will be assigned to one of the IDs in this list  
FRONTEND_HTTP_PORT = This is the port that the frontend HTTP service listens on  
FRONTEND_TCP_PORT = This is the port that the frontend TCP service listens on 
CACHE_SIZE = This is the size of the frontends cache  
ORDER_SERVICE_ID = This tells the order service replicas which ID, Port, and Address to use, The replica will then use this position in the ID list, address list, and port list, this can be 0, 1, or 2. This must be set in the terminal before running the order service replicas, it is not declared in the .env, if it is not set order service will use the default value of 2. More about this variables is found in the Running services section. 

## Understanding the clients:  
There are 2 clients. load_test_client.py is an automated client that creates 5 client copies and performs the algorithm as described while also measuring response times. client.py is a client which can perform the client algorithm as defined in the project, without the response measurements, OR can be set to human mode where it has a basic human interface for a user to query, buy, and check orders manually.

