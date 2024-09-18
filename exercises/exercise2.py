from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class RipMessage(MessageStub):
    def __init__(self, sender: int, destination: int, table):
        super().__init__(sender, destination)
        self.table = table

    def __str__(self):
        return f'RipMessage: {self.source} -> {self.destination} : {self.table}'

class RoutableMessage(MessageStub):
    def __init__(self, sender: int, destination: int, first_node: int, last_node: int, content):
        super().__init__(sender, destination)
        self.content = content
        self.first_node = first_node
        self.last_node = last_node

    def __str__(self):
        return f'RoutableMessage: {self.source} -> {self.destination} : {self.content}'




class RipCommunication(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        
        self.neighbors = [] # generate an appropriate list
        self.neighbors.append((self.index() + 1) % self.number_of_devices())
        self.neighbors.append((self.index() - 1 + self.number_of_devices()) % self.number_of_devices())

        self.routing_table = dict()

    def run(self):
        for neigh in self.neighbors:
            self.routing_table[neigh] = (neigh, 1)
        self.routing_table[self.index()] = (self.index(), 0)
        for neigh in self.neighbors:
            self.medium().send(RipMessage(self.index(), neigh, self.routing_table))

        while True:
            ingoing = self.medium().receive()
            if ingoing is None:
                # this call is only used for synchronous networks
                self.medium().wait_for_next_round()
                if self.routing_table_complete():
                    break
                continue

            if type(ingoing) is RipMessage:
                print(f"Device {self.index()}: Got new table from {ingoing.source}")
                returned_table = self.merge_tables(ingoing.source, ingoing.table)
                if returned_table is not None:
                    self.routing_table = returned_table
                    for neigh in self.neighbors:
                        self.medium().send(RipMessage(self.index(), neigh, self.routing_table))

            if type(ingoing) is RoutableMessage:
                print(f"Device {self.index()}: Routing from {ingoing.first_node} to {ingoing.last_node} via #{self.index()}: [#{ingoing.content}]")
                if ingoing.last_node is self.index():
                    print(f"\tDevice {self.index()}: delivered message from {ingoing.first_node} to {ingoing.last_node}: {ingoing.content}")
                    continue
                if self.routing_table[ingoing.last_node] is not None:
                    (next_hop, distance) = self.routing_table[ingoing.last_node]
                    self.medium().send(RoutableMessage(self.index(), next_hop, ingoing.first_node, ingoing.last_node, ingoing.content))
                    continue
                print(f"\tDevice {self.index()}:  DROP Unknown route #{ingoing.first_node} to #{ingoing.last_node} via #{self.index}, message #{ingoing.content}")

            # this call is only used for synchronous networks
            self.medium().wait_for_next_round()

    # src: int = neigh number
    # table: dict (int, int) = routing_table
        # row: int
    # table is the src's routing_table
    def merge_tables(self, src: int, table: dict):
        # return None if the table does not change
        temp_table = self.routing_table.copy()
        
        
        ## not my code! Copied from a solution
        # for destination, (link, distance) in table.items():
        #     if destination not in temp_table:
        #         temp_table[destination] = (src, distance + 1)
        #         continue
        #     if distance + 1 < temp_table[destination][1]:
        #         temp_table[destination] = (src, distance + 1)
            
        
        
        ## I do not get why this does not work. I am positive that I follow the pseudocode, but clearly something is misunderstood
        for rr_destination, (rr_link, rr_cost) in table.items():
            if rr_link != src:
                table[rr_destination] = (src, rr_cost + 1)
                
                if (rr_destination not in self.routing_table):
                    self.routing_table[rr_destination] = (rr_link, rr_cost)
                else:
                    for rl_destination, (rl_link, rl_cost) in self.routing_table.items():
                        if rr_destination == rl_destination and (rr_cost < rl_cost or rl_link == src):
                            self.routing_table[rl_destination] = table[rr_destination]
                            # table[i][1] < self.routing_table[i][1]    --> remote node has better route
                            # self.routing_table[0][0] == self.index()  --> remote node is more authorative
        
        
        ## This code comes from a solution
        if temp_table == self.routing_table:
            return None
        
        return temp_table    
    
    def routing_table_complete(self) -> bool:
        if len(self.routing_table) < self.number_of_devices() - 1:
            return False
        for row in self.routing_table:
            (link, distance) = self.routing_table[row]
            if distance > (self.number_of_devices() / 2):
                return False
            return True


    def print_result(self):
        print(f'\tDevice {self.index()} has routing table: {self.routing_table}')