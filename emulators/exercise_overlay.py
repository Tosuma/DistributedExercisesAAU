from random import randint
from threading import Thread
from time import sleep
from PyQt6.QtWidgets import QWidget, QApplication, QHBoxLayout, QVBoxLayout, QPushButton, QTabWidget, QLabel, QLineEdit
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from sys import argv
from math import cos, sin, pi
from emulators.AsyncEmulator import AsyncEmulator
from emulators.MessageStub import MessageStub

from emulators.table import Table
from emulators.SteppingEmulator import SteppingEmulator

def circle_button_style(size, color = "black"):
	return f'''
	QPushButton {{
		background-color: transparent; 
		border-style: solid; 
		border-width: 2px; 
		border-radius: {int(size/2)}px; 
		border-color: {color}; 
		max-width: {size}px; 
		max-height: {size}px; 
		min-width: {size}px; 
		min-height: {size}px;
	}}
	QPushButton:hover {{
		background-color: gray;
		border-width: 2px; 
	}}
	QPushButton:pressed {{
		background-color: transparent; 
		border-width: 1px
	}}
	'''

class Window(QWidget):
	h = 640
	w = 600
	device_size = 80
	last_message = None
	buttons:dict[int, QPushButton] = {}
	windows = list()

	def __init__(self, elements, restart_function, emulator:SteppingEmulator):
		super().__init__()
		self.emulator = emulator
		self.setFixedSize(self.w, self.h)
		layout = QVBoxLayout()
		tabs = QTabWidget()
		tabs.addTab(self.main(elements, restart_function), 'Main')
		tabs.addTab(self.controls(), 'controls')
		layout.addWidget(tabs)
		self.setLayout(layout)
		self.setWindowTitle("Stepping Emulator")
		self.setWindowIcon(QIcon("icon.ico"))

	def coordinates(self, center, r, i, n):
		x = sin((i*2*pi)/n)
		y = cos((i*2*pi)/n)
		if x < pi:
			return int(center[0] - (r*x)), int(center[1] - (r*y))
		else:
			return int(center[0] - (r*-x)), int(center[1] - (r*y))

	def show_device_data(self, device_id):
		def show():
			received:list[MessageStub] = list()
			sent:list[MessageStub] = list()
			for message in self.emulator._list_messages_received:
				if message.destination == device_id:
					received.append(message)
				if message.source == device_id:
					sent.append(message)
			if len(received) > len(sent):
				for _ in range(len(received)-len(sent)):
					sent.append("")
			elif len(sent) > len(received):
				for _ in range(len(sent)-len(received)):
					received.append("")
			content = list()
			for i in range(len(received)):
				if received[i] == "":
					msg = str(sent[i]).replace(f'{sent[i].source} -> {sent[i].destination} : ', "").replace(f'{sent[i].source}->{sent[i].destination} : ', "")
					content.append(["", received[i], str(sent[i].destination), msg])
				elif sent[i] == "":
					msg = str(received[i]).replace(f'{received[i].source} -> {received[i].destination} : ', "").replace(f'{received[i].source}->{received[i].destination} : ', "")
					content.append([str(received[i].source), msg, "", sent[i]])
				else:
					sent_msg = str(sent[i]).replace(f'{sent[i].source} -> {sent[i].destination} : ', "").replace(f'{sent[i].source}->{sent[i].destination} : ', "")
					received_msg = str(received[i]).replace(f'{received[i].source} -> {received[i].destination} : ', "").replace(f'{received[i].source}->{received[i].destination} : ', "")
					content.append([str(received[i].source), received_msg, str(sent[i].destination), sent_msg])
			content.insert(0, ['Source', 'Message', 'Destination', 'Message'])
			table = Table(content, title=f'Device #{device_id}')
			self.windows.append(table)
			table.setFixedSize(300, 500)
			table.show()
			return table
		return show
	
	def show_all_data(self):
		content = []
		messages = self.emulator._list_messages_sent
		message_content = []
		for message in messages:
			temp = str(message)
			temp = temp.replace(f'{message.source} -> {message.destination} : ', "")
			temp = temp.replace(f'{message.source}->{message.destination} : ', "")
			message_content.append(temp)

		content = [[str(messages[i].source), str(messages[i].destination), message_content[i], str(i)] for i in range(len(messages))]
		content.insert(0, ['Source', 'Destination', 'Message', 'Sequence number'])
		table = Table(content, title=f'All data')
		self.windows.append(table)
		table.setFixedSize(500, 500)
		table.show()
		return table

	def show_queue(self):
		content = [["Source", "Destination", "Message"]]
		if self.emulator.parent is AsyncEmulator:
			queue = self.emulator._messages.values()
		elif self.emulator:
			queue = self.emulator._last_round_messages.values()
		for messages in queue:
			for message in messages:
				message_stripped = str(message).replace(f'{message.source} -> {message.destination} : ', "").replace(f'{message.source}->{message.destination} : ', "")
				content.append([str(message.source), str(message.destination), message_stripped])
		table = Table(content, "Message queue")
		self.windows.append(table)
		table.setFixedSize(500, 500)
		table.show()
		return table

	def pick(self):
		def execute():
			device = int(footer_content['Device: '].text())
			index = int(footer_content['Message: '].text())
			if self.emulator.parent is AsyncEmulator:
				self.emulator._messages[device].append(self.emulator._messages[device].pop(index))
			else:
				self.emulator._last_round_messages[device].append(self.emulator._last_round_messages[device].pop(index))
			window.destroy(True, True)

		self.emulator.print_transit()
		keys = []
		if self.emulator.parent is AsyncEmulator:
			messages = self.emulator._messages
		else:
			messages = self.emulator._last_round_messages
		if len(messages) == 0:
			return
		for item in messages.items():
			keys.append(item[0])
		keys.sort()
		window = QWidget()
		layout = QVBoxLayout()
		header = QLabel("Pick a message to be transmitted next")
		layout.addWidget(header)
		max_size = 0
		for m in messages.values():
			if len(m) > max_size:
				max_size = len(m)
		content = [[str(messages[key][i]) if len(messages[key]) > i else " " for key in keys] for i in range(max_size)]
		content.insert(0, [f'Device {key}' for key in keys])
		content[0].insert(0, "Message #")
		for i in range(max_size):
			content[i+1].insert(0, str(i))
		table = Table(content, "Pick a message to be transmitted next")
		layout.addWidget(table)
		footer_content = {"Device: ": QLineEdit(), "Message: ": QLineEdit()}
		for entry in footer_content.items():
			frame = QHBoxLayout()
			frame.addWidget(QLabel(entry[0]))
			frame.addWidget(entry[1])
			layout.addLayout(frame)

		button = QPushButton('Confirm')
		button.clicked.connect(execute)
		layout.addWidget(button)

		window.setLayout(layout)
		window.show()
		self.windows.append(window)
		


	def stop_stepper(self):
		self.emulator.listener.stop()
		self.emulator.listener.join()

	def end(self):
		self.emulator._stepping = False
		while not self.emulator.all_terminated():
			self.set_device_color()
		Thread(target=self.stop_stepper, daemon=True).start()
	
	def set_device_color(self):
		sleep(.1)
		messages = self.emulator._list_messages_sent if self.emulator.last_action == "send" else self.emulator._list_messages_received
		if len(messages) != 0:
			last_message = messages[len(messages)-1]
			if not last_message == self.last_message:
				for button in self.buttons.values():
					button.setStyleSheet(circle_button_style(self.device_size))
				if last_message.source == last_message.destination:
					self.buttons[last_message.source].setStyleSheet(circle_button_style(self.device_size, 'yellow'))
				else:
					self.buttons[last_message.source].setStyleSheet(circle_button_style(self.device_size, 'green'))
					self.buttons[last_message.destination].setStyleSheet(circle_button_style(self.device_size, 'red'))
				self.last_message = last_message

	def step(self):
		self.emulator._single = True
		if self.emulator.all_terminated():
			Thread(target=self.stop_stepper, daemon=True).start()
		self.set_device_color()

	def restart_algorithm(self, function):
		self.windows.append(function())

	def main(self, num_devices, restart_function):
		main_tab = QWidget()
		green = QLabel("green: source", main_tab)
		green.setStyleSheet("color: green;")
		green.move(5, 0)
		green.show()
		red = QLabel("red: destination", main_tab)
		red.setStyleSheet("color: red;")
		red.move(5, 20)
		red.show()
		yellow = QLabel("yellow: same device", main_tab)
		yellow.setStyleSheet("color: yellow;")
		yellow.move(5, 40)
		yellow.show()
		layout = QVBoxLayout()
		device_area = QWidget()
		device_area.setFixedSize(500, 500)
		layout.addWidget(device_area)
		main_tab.setLayout(layout)
		for i in range(num_devices):
			x, y = self.coordinates((device_area.width()/2, device_area.height()/2), (device_area.height()/2) - (self.device_size/2), i, num_devices)
			button = QPushButton(f'Device #{i}', main_tab)
			button.resize(self.device_size, self.device_size)
			button.setStyleSheet(circle_button_style(self.device_size))
			button.move(x, int(y - (self.device_size/2)))
			button.clicked.connect(self.show_device_data(i))
			self.buttons[i] = button
		
		button_actions = {'Step': self.step, 'End': self.end, 'Restart algorithm': lambda: self.restart_algorithm(restart_function), 'Show all messages': self.show_all_data, 'Show queue': self.show_queue, 'Switch emulator': self.emulator.swap_emulator, 'Pick': self.pick}
		inner_layout = QHBoxLayout()
		index = 0
		for action in button_actions.items():
			index+=1
			if index == 4:
				layout.addLayout(inner_layout)
				inner_layout = QHBoxLayout()
			button = QPushButton(action[0])
			button.clicked.connect(action[1])
			inner_layout.addWidget(button)
		layout.addLayout(inner_layout)

		return main_tab

	def controls(self):
		controls_tab = QWidget()
		content = {
			'Space': 	'Step a single time through messages', 
			'f': 		'Fast forward through messages', 
			'Enter': 	'Kill stepper daemon and run as an async emulator',
			'tab': 		'Show all messages currently waiting to be transmitted',
			's':		'Pick the next message waiting to be transmitted to transmit next',
			'e':		'Toggle between sync and async emulation'
		}
		main = QVBoxLayout()
		main.setAlignment(Qt.AlignmentFlag.AlignTop)
		controls = QLabel("Controls")
		controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
		main.addWidget(controls)
		top = QHBoxLayout()
		key_layout = QVBoxLayout()
		value_layout = QVBoxLayout()
		for key in content.keys():
			key_layout.addWidget(QLabel(key))
			value_layout.addWidget(QLabel(content[key]))
		top.addLayout(key_layout)
		top.addLayout(value_layout)
		main.addLayout(top)
		controls_tab.setLayout(main)
		return controls_tab
	
	def closeEvent(self, event):
		Thread(target=self.end).start()
		event.accept()

if __name__ == "__main__":
	app = QApplication(argv)
	window = Window(argv[1] if len(argv) > 1 else 10, lambda: print("Restart function"))

	app.exec()
