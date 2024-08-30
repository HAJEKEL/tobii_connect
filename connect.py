from tobiiglassesctrl.controller import TobiiGlassesController

class PatchedTobiiGlassesController(TobiiGlassesController):
    def __init__(self, *args, **kwargs):
        self.data_socket = None  # Initialize data_socket
        super().__init__(*args, **kwargs)

    def __mksock__(self):
        sock = super()._TobiiGlassesController__mksock()
        sock.setsockopt(socket.SOL_SOCKET, 25, self.iface_name.encode('utf-8') + b'\0')
        return sock

    def close(self):
        if self.data_socket:  # Ensure data_socket exists before trying to close
            self.data_socket.close()
        super().close()

# Instantiate the patched controller
controller = PatchedTobiiGlassesController("fe80::52bc:2e3e:d916:f34e%enp0s31f6")
