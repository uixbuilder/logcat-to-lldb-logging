import subprocess


class ActiveSessionLogger:
    """A logger that writes messages to the LLDB console via TTY."""
    
    _tty = None  # Cached TTY (static variable)

    def __init__(self, tag="Logger"):
        """
        Initialize a Logger instance with a tag.
        :param tag: A string identifier for the log sender (e.g., "Logcat", "Listener").
        """
        self.tag = tag

    @property
    def tty(self):
        """Lazily fetch the TTY only when needed."""
        if ActiveSessionLogger._tty is None:
            ActiveSessionLogger._tty = self.find_lldb_tty()
        return ActiveSessionLogger._tty

    @staticmethod
    def find_lldb_tty():
        """Finds the TTY of the LLDB console inside Xcode."""
        try:
            xcode_pid = subprocess.check_output(
                "ps -A | grep -m1 MacOS/Xcode | awk '{print $1}'", shell=True
            ).decode().strip()
            if not xcode_pid:
                return None

            tty_line = subprocess.check_output(
                f"lsof -p {xcode_pid} | grep -m2 dev/ttys | tail -1 | awk '{{print $9}}'",
                shell=True
            ).decode().strip()
            
            if not tty_line:
                return None

            return tty_line
        except Exception as e:
            print(f"Error finding LLDB TTY: {e}")
            return None

    def log(self, message):
        """Logs a message to the LLDB console with the object's tag."""
        if self.tty:
            formatted_message = f"[{self.tag}] {message}"
            cmd = f"echo '{formatted_message}' > {self.tty}"
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def redirect(self, message):
        """Redirects a message to the LLDB console."""
        if self.tty:
            cmd = f"echo '{message}' > {self.tty}"
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
