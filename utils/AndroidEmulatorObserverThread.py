import lldb
import threading
import subprocess
import re
from .ActiveSessionLogger import ActiveSessionLogger


class AndroidEmulatorObserverThread(threading.Thread):
    def __init__(self, debugger, clear_history = False):
        super().__init__(daemon=True)
        self.debugger = debugger
        self.process = None
        self.running = False
        self.logger = ActiveSessionLogger(tag="ADB")
        self.clear_history = clear_history

    def run(self):
        """Runs adb logcat in a subprocess and filters logs."""
        if self.clear_history:
            self.clear_logcat()
            
        self.start_logcat()

    def clear_logcat(self):
        """Clears the logcat buffer."""
        subprocess.run(["/opt/homebrew/bin/adb", "logcat", "-c"], shell=False)

    def start_logcat(self):
        """Starts the logcat process and filters logs."""
        cmd = ["/opt/homebrew/bin/adb", "logcat"]

        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, text=True, universal_newlines=True, bufsize=1)
            self.running = True
            
            if self.process.stdout is None:
                self.logger.log("No stdout from adb logcat!")
                return
            
            log_type_map = {
                "E": "‼️",
                "W": "⚠️",
                "I": "  ",
                "D": "🐞",
                "V": "👀"
            }
            
            log_pattern = None
            bundle_id_prefix = self.debugger.GetTargetAtIndex(0).GetProcess().GetProcessInfo().GetName().lower()
            # Define the regular expression to match the application bundle ID.
            bundle_id_pattern = re.compile(rf'([a-zA-Z0-9_.]*\.{bundle_id_prefix})')
            
            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break
                
                if log_pattern is None:
                    # Try to find the bundle ID in the current line.
                    match = bundle_id_pattern.search(line)
                    if match:
                        # Now we can define the regex for parsing ADB log messages.
                        bundle_id = match.group(1)
                        self.logger.log(f"Logcat started! Waiting for logs from {bundle_id}")
                        log_pattern = re.compile(rf'.+([A-Z])\s+{bundle_id}(\.([^\s]+)?)?:\s(.+)$')
                    else:
                        continue
                
                # From this point on, the parser regex is ready to process log lines.
                match = log_pattern.match(line)
                if match:
                    log_level, _, tag, message = match.groups()
                    log_type = log_type_map.get(log_level, "log")
                    formatted_line = f'🤖{log_type}[{tag}]\t{message.strip()}' if tag else f'🤖\t{log_type}\t{message.strip()}'
                    self.logger.redirect(formatted_line)
        
        except Exception as e:
            self.logger.log(f"Logcat error: {e}")

    def stop(self):
        """Stops the logcat process if running."""
        if self.process:
            self.running = False
            self.process.terminate()
            self.process = None
            self.logger.log("Logcat stopped.")

    def __del__(self):
        """Ensures cleanup when the thread is deallocated."""
        self.stop()
        self.clear_logcat()
        self.logger.log("Cleanup complete.")
