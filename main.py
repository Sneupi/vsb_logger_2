import tkinter as tk
import threading
import serial
import queue
import tkpanels as tkp

class SerialThread(threading.Thread):
    def __init__(self, serial_port, baud_rate, data_queue):
        super().__init__()
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.data_queue = data_queue
        self.running = False
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate)
            self.running = True
        except serial.SerialException as e:
            print(f"Error opening serial port: {e}")
            return

        while self.running:
            try:
                if self.ser.in_waiting:
                    data = self.ser.readline().decode('utf-8').strip()
                    self.data_queue.put(data)
            except serial.SerialException as e:
                print(f"Serial read error: {e}")
                self.running = False
            except UnicodeDecodeError as e:
                print(f"Unicode error: {e}")

    def stop(self):
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except serial.SerialException as e:
                print(f"Error closing serial port: {e}")

class SerialApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("App")
        self.root.geometry("1280x720")
        self.root.resizable(False, False)
        
        self.data_queue = queue.Queue()
        self.serial_thread = None

        self.setup_gui()
        self.root.after(100, self.process_serial_data)

    def setup_gui(self):
        
        self.controls = tkp.ControlsFrame(self.root)
        self.controls.place(relx=0, rely=0, relwidth=0.4, relheight=0.4)
        
        self.serial_setup = tkp.SerialSetup(self.root, self.connect_serial)
        self.serial_setup.place(relx=0, rely=0.9, relwidth=0.4, relheight=0.1)

        self.terminal = tkp.CLIFrame(self.root, self.send_data)
        self.terminal.place(relx=0, rely=0.4, relwidth=0.4, relheight=0.5)

    def connect_serial(self, event=None):
        port = self.serial_setup.get_port()
        baud_rate = self.serial_setup.get_baud()
        
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()

        if port and baud_rate:
            self.serial_thread = SerialThread(port, int(baud_rate), self.data_queue)
            self.serial_thread.daemon = True
            self.serial_thread.start()

    def process_serial_data(self):
        while not self.data_queue.empty():
            data = self.data_queue.get()
            self.log_message(data)
        self.root.after(100, self.process_serial_data)

    def send_data(self, event=None):
        data = self.terminal.get_entry()
        if self.serial_thread and self.serial_thread.ser and self.serial_thread.ser.is_open:
            try:
                self.serial_thread.ser.write(data.encode('utf-8'))
                self.log_message(data)
            except serial.SerialException as e:
                print(f"Serial write error: {e}")

    def log_message(self, message):
        self.terminal.log_message(message)

    def on_closing(self):
        if self.serial_thread and self.serial_thread.running:
            self.serial_thread.stop()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = SerialApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
