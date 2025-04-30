import socket
import threading
import json

class NetworkManager:
    def __init__(self):
        self.is_host = False
        self.socket = None
        self.clients = []
        self.server_address = None
        self.connected = False
        
    def create_server(self, port=5555):
        """Create a server for hosting a multiplayer game"""
        self.is_host = True
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', port))
        self.socket.listen(5)
        self.connected = True
        
        # Start a thread to accept connections
        threading.Thread(target=self._accept_connections, daemon=True).start()
        
        return True
        
    def connect_to_server(self, host, port=5555):
        """Connect to an existing game server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.server_address = (host, port)
            self.connected = True
            
            # Start a thread to receive data
            threading.Thread(target=self._receive_data_thread, daemon=True).start()
            
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
            
    def _accept_connections(self):
        """Accept incoming connections (runs in a separate thread)"""
        while self.connected:
            try:
                client_socket, address = self.socket.accept()
                self.clients.append((client_socket, address))
                
                # Start a thread to handle this client
                threading.Thread(target=self._handle_client, args=(client_socket, address), daemon=True).start()
                
                print(f"Client connected: {address}")
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break
                
    def _handle_client(self, client_socket, address):
        """Handle communication with a connected client"""
        while self.connected:
            try:
                data = client_socket.recv(1024)
                if not data:
                    break
                    
                # Process received data
                self._process_received_data(data, client_socket)
                
                # Forward data to other clients
                self._broadcast(data, client_socket)
            except Exception as e:
                print(f"Error handling client {address}: {e}")
                break
                
        # Remove client when disconnected
        if (client_socket, address) in self.clients:
            self.clients.remove((client_socket, address))
            client_socket.close()
            print(f"Client disconnected: {address}")
            
    def _receive_data_thread(self):
        """Receive data from the server (runs in a separate thread)"""
        while self.connected:
            try:
                data = self.socket.recv(1024)
                if not data:
                    break
                    
                # Process received data
                self._process_received_data(data)
            except Exception as e:
                print(f"Error receiving data: {e}")
                break
                
        self.connected = False
        print("Disconnected from server")
        
    def _process_received_data(self, data, sender=None):
        """Process data received from the network"""
        try:
            # Parse the JSON data
            message = json.loads(data.decode('utf-8'))
            
            # Handle different message types
            if message.get('type') == 'car_update':
                # Update opponent car position
                car_data = message.get('data', {})
                # This would be handled by the game to update opponent cars
                print(f"Received car update: {car_data}")
        except Exception as e:
            print(f"Error processing received data: {e}")
            
    def _broadcast(self, data, sender):
        """Broadcast data to all connected clients except the sender"""
        for client, _ in self.clients:
            if client != sender:
                try:
                    client.sendall(data)
                except Exception as e:
                    print(f"Error broadcasting data: {e}")
                    
    def send_data(self, data_dict):
        """Send data to the server or clients"""
        if not self.connected:
            return False
            
        try:
            # Convert data to JSON
            data = json.dumps(data_dict).encode('utf-8')
            
            if self.is_host:
                # If host, broadcast to all clients
                self._broadcast(data, None)
            else:
                # If client, send to server
                self.socket.sendall(data)
                
            return True
        except Exception as e:
            print(f"Error sending data: {e}")
            return False
            
    def close(self):
        """Close the network connection"""
        self.connected = False
        
        if self.is_host:
            # Close all client connections
            for client, _ in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients = []
            
        # Close the socket
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
class NetworkManager:
    def __init__(self):
        self.connected = False
        self.party_code = None
        
    def connect(self, party_code=None):
        # Simulate connection
        self.connected = True
        self.party_code = party_code
        return True
        
    def disconnect(self):
        self.connected = False
        self.party_code = None
        
    def send_data(self, data):
        # Simulate sending data
        if not self.connected:
            return False
        return True
        
    def receive_data(self):
        # Simulate receiving data
        if not self.connected:
            return None
        
        # Return dummy data
        return {
            'players': [
                {
                    'id': 'opponent1',
                    'x': 400,
                    'y': 300,
                    'angle': 0,
                    'speed': 0
                }
            ]
        }