import tkinter as tk
import socket
import threading

# Host IP and port (0.0.0.0 to listen to anyone, port 40001 for TSL?)
UDP_HOST = '0.0.0.0'
UDP_PORT = 40001

# Now lets make a sexy sexy gui, and call it TSL UMD Listener.
class TSLGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TSL UM Listener")
        self.frames = {}
        self.stats = {'v3count': 0, 'v4count': 0, 'errors': 0}

        for address in range(1, 9):
            frame = tk.Frame(self, width=200, height=150, relief=tk.RAISED, borderwidth=2)
            frame.pack(side=tk.LEFT, padx=10, pady=10)
            label_address = tk.Label(frame, text=f"Address {address}", font=("Arial", 12, "bold"))
            label_address.pack(pady=10)
            label_tally = tk.Label(frame, text="", font=("Arial", 12))
            label_tally.pack()
            label_data = tk.Label(frame, text="", font=("Arial", 10))
            label_data.pack()
            self.frames[address] = (frame, label_tally, label_data)

        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()

    def receive_messages(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((UDP_HOST, UDP_PORT))

        try:
            while True:
                data, _ = udp_socket.recvfrom(1024)
                print(f"Received UDP message: {data}")
                self.process_message(data)
        except Exception as e:
            print(f"Error receiving UDP message: {e}")
        finally:
            udp_socket.close()

    def process_message(self, data):
        if len(data) == 18 or len(data) == 22:
            if data[0] >= 128 and (data[1] & 0x40) == 0:
                addr = data[0] & 0x7f
                msg = data[2:18].decode('utf-8').strip()

                if len(data) == 18:
                    bright = (data[1] & 0x30) >> 4
                    tallybits = data[1] & 0x0f
                    print(f"Processing V3 message for address {addr}, message: {msg}, tallybits: {tallybits}")
                    self.update_gui(addr, msg, tallybits & 0x01, tallybits & 0x02, (tallybits & 0x04) != 0, (tallybits & 0x08) != 0)
                    self.stats['v3count'] += 1
                elif len(data) == 22:
                    if self.checksum(data[0:18]) == data[18] and data[19] == 0x02:
                        print(f"Processing V4 message for address {addr}, message: {msg}")
                        self.update_gui(addr, msg, data[20] & 0x03, (data[20] >> 4) & 0x03, data[21] & 0x03, (data[21] >> 4) & 0x03)
                        self.stats['v4count'] += 1
                    else:
                        print("Bad V4 packet")

    def update_gui(self, addr, msg, tally1, tally2, tally3, tally4):
        if 1 <= addr <= 8:
            frame, label_tally, label_data = self.frames[addr]
            tally_status = [
                ("PROGRAM", "red") if tally1 else None,
                ("PREVIEW", "green") if tally2 else None,
                ("Tally 3", "orange") if tally3 else None,
                ("Tally 4", "orange") if tally4 else None
            ]

            display_status = next((status for status in tally_status if status is not None), None)

            if display_status:
                text_display, color_display = display_status
            else:
                text_display = "Blank"
                color_display = "grey"

            label_tally.config(text=text_display, fg=color_display)
            label_data.config(text=f"{msg}")
            frame.config(bg=color_display)

    def checksum(self, data):
        return (sum(data) % 128) & 0x7f

def main():
    gui = TSLGUI()
    gui.mainloop()

if __name__ == "__main__":
    main()
