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
            
            self.logger.log("Logcat started! Waiting for logs...")

            bundle_id_prefix = self.debugger.GetTargetAtIndex(0).GetProcess().GetProcessInfo().GetName()
            
            if not bundle_id_prefix:
                self.logger.log("No bundle ID detected. Filtering disabled.")
            
            log_type_map = {
                "E": "‼️",
                "W": "⚠️",
                "I": "",
                "D": "🐞",
                "V": "👀"
            }

            log_pattern = re.compile(rf'.+([A-Z])\s+(\S+{bundle_id_prefix}.{bundle_id_prefix}):\s(.+)$')

            for line in iter(self.process.stdout.readline, ''):
                if not self.running:
                    break

                match = log_pattern.match(line)
                if match:
                    log_level, tag, message = match.groups()
                    log_type = log_type_map.get(log_level, "log")
                    formatted_line = f'🤖{log_type} {message.strip()}'
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
