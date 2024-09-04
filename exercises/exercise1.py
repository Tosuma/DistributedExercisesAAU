from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class GossipMessage(MessageStub):

    def __init__(self, sender: int, destination: int, secrets):
        super().__init__(sender, destination)
        # we use a set to keep the "secrets" here
        self.secrets = secrets

    def __str__(self):
        return f'{self.source} -> {self.destination} : {self.secrets}'


class Gossip(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        # for this exercise we use the index as the "secret", but it could have been a new routing-table (for instance)
        # or sharing of all the public keys in a cryptographic system
        self._secrets = set([index])

    def run(self):
        next_to_call: int = (self.index() + 1) % self.number_of_devices()
        while True:
            if len(self._secrets) == self.number_of_devices():
                for i in range(0, self.number_of_devices()):
                    if i == self.index: continue
                    self.medium().send(GossipMessage(self.index(), i, self._secrets))
                print(f'Thread {self.index()} returns')
                return
            
            if next_to_call == self.index():
                next_to_call = (next_to_call + 1) % self.number_of_devices()
                continue

            self.medium().send(GossipMessage(self.index(), next_to_call, self._secrets))
        
            ingoing = self.medium().receive_all()
            if ingoing is None:
                continue
            else:
                for received in ingoing:
                    self._secrets.update(received.secrets)

            next_to_call = (next_to_call + 1) % self.number_of_devices()
            self.medium().wait_for_next_round()

    def print_result(self):
        print(f'\tDevice {self.index()} got secrets: {self._secrets}')
    