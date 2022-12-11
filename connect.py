import socket
import threading
import logging
import time

class ServerCreationError(Exception):
    pass

class ConnectionDropException(Exception):
    pass

class Server:
    def __init__(self, hostname: str, port: int):
        logging.debug("Server initialization started")
        logging.debug(f"Configured server address: [ {hostname}:{port} ]")

        self.socket = None
        self.running = True
        self.client_pool = []
        self.client_addr_table = {}
        self.client_thread_table = {}

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((hostname, port))
            self.socket.listen(16)
        except:
            logging.error("Error during server socket creation")
            self.shutdown()
            raise ServerCreationError

        def server_loop():
            while True:
                try:
                    client, addr = self.socket.accept()

                except OSError:
                    # wait a 1 sec timeout and check what happened
                    time.sleep(1)
                    if not self.running:
                        return
                    else:
                        logging.critical("Error accepting new connections from socket, shutting down")
                        self.shutdown()
                        return

                logging.info(f"Incoming connection from [ {addr[0]}:{addr[1]} ]")
                self.client_pool.append(client)
                self.client_addr_table[client] = addr
                logging.info(f"Starting new thread for client request...")
                new_client_thread = threading.Thread(target = self.client_connection_handler, args = (client,))
                self.client_thread_table[client] = new_client_thread
                new_client_thread.start()

        self.listening_thread = threading.Thread(target = server_loop, args = ())

        def read_from_cmdline():
            while True:
                data = input()
                if self.running:
                    pass
                else:
                    return

        self.inputThread = threading.Thread(target=read_from_cmdline, args=())
        logging.debug("Server initialization completed")

    def run(self):
        logging.info("Server status: [[ UP ]]")
        self.listening_thread.start()
        self.inputThread.start()
        logging.info("Listening for connections...")

    def receive_from(self, client, buffer_size = 4096, encoding = 'utf-8'):
        data = None
        try:
            data_raw = client.recv(buffer_size)
            data = data_raw.decode(encoding)
            if len(data_raw) == 0:
                logging.warning(f"null data received from [ {self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} ], testing if the connection is alive...")
                self.send(client, 0, ping_test=True)
        except OSError:
            raise ConnectionDropException

        if len(data_raw) > 0:
            logging.info(f"Data received from [ {self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} ], length = {len(data)} Bytes")
        return data

    def send(self, client, data, ping_test = False):
        data_bytes = str(data).encode('utf-8')
        if ping_test:
            logging.info(f"Pinging [ {self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} ]")
        else:
            logging.info(f"Sending data to [ {self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} ], length = {len(data_bytes)} Bytes")
        try:
            client.send(data_bytes)
            return
        except BrokenPipeError:
            raise ConnectionDropException

    def broadcast(self, data):
        for client in self.client_pool:
            try:
                self.send(client, data)
            except ConnectionDropException:
                pass

    def client_connection_handler(self, client: socket):
        pass

    def close_connection(self, client: socket):
        client.close()
        try:
            del self.client_addr_table[client]
            self.client_pool.remove(client)
        except KeyError:
            pass


        # make sure the client request processing threads have done running
        if client in self.client_thread_table.keys():
            try:
                self.client_thread_table[client].join(timeout = 5)
            except RuntimeError:
                pass

            del self.client_thread_table[client]

        return

    def connection_drop_handler(self, client: socket):
        try:
            logging.warning(f"{self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} Connection dropped")
        except KeyError:
            pass

        self.close_connection(client)
        return

    def shutdown(self):
        if self.running:
            logging.info("Shutting down... ")

            # Close self listening socket
            if self.socket:
                self.socket.close()

            for cli in self.client_pool:
                self.close_connection(cli)

            self.running = False
            logging.info("Server status: [[ DOWN ]]")