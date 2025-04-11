import lldb
import threading
from .ActiveSessionLogger import ActiveSessionLogger
from .AndroidEmulatorObserverThread import AndroidEmulatorObserverThread


class DebugSessionListeningThread(threading.Thread):
    def __init__(self, debugger):
        super().__init__(daemon=True)
        self.debugger = debugger
        self.logger = ActiveSessionLogger(tag="Listener")  # Use a distinct tag for ListeningThread
        self.logcat_thread = AndroidEmulatorObserverThread(self.debugger)
        self.condition = threading.Condition()
        
    def wait_for_next_event(self, process):
        """Waits for the next LLDB process state event."""
        broadcaster = process.GetBroadcaster()
        listener = lldb.SBListener("EventsListener")
        broadcaster.AddListener(listener, lldb.SBProcess.eBroadcastBitStateChanged)
        event = lldb.SBEvent()

        while not listener.WaitForEventForBroadcasterWithType(
                  5, broadcaster, lldb.SBProcess.eBroadcastBitStateChanged, event):
            pass

    def run(self):
        """Main loop for listening to debugger events."""
        process = None
        
        # Wait for a valid debugger process
        while True:
            if self.debugger.GetNumTargets() > 0:
                process = self.debugger.GetTargetAtIndex(0).GetProcess()
            else:
                process = None
            if process and process.IsValid():
                break
                
            with self.condition:
                self.logger.log("Waiting for debugger!...")
                self.condition.wait(timeout=0.5)
    
        self.logger.log("Listening debugger events started.")
        last_state = None

        while True:
            process_state = process.GetState()
            if process_state == last_state or process_state == lldb.eStateInvalid:
                self.wait_for_next_event(process)
                continue
                
            last_state = process_state
            state_str = lldb.SBDebugger.StateAsCString(process_state)
            self.logger.log(f"Current process state: {state_str}")

            if process_state == lldb.eStateRunning:
                if not self.logcat_thread.is_alive():
                    if self.logcat_thread.clear_history:
                        self.logger.log("Starting Logcat redirection and clearing history...")
                    else:
                        self.logger.log("Resuming Logcat redirection without clearing history...")
                    self.logcat_thread.start()

            elif process_state in [lldb.eStateStopped, lldb.eStateCrashed]:
                if self.logcat_thread.is_alive():
                    self.logger.log("Pausing Logcat redirection...")
                    self.logcat_thread.stop()
                    self.logcat_thread.join()
                    self.logcat_thread = None
                    self.logcat_thread = AndroidEmulatorObserverThread(self.debugger)

            elif process_state in [lldb.eStateExited, lldb.eStateDetached]:
                self.logger.log("Process exited/detached. Cleaning up Logcat...")
                self.logcat_thread.stop()
                break
                
    def __del__(self):
        """Ensures cleanup when the thread is deallocated."""
        if self.logcat_thread is not None:
            self.logcat_thread.stop()
        self.logger.log("Stopping ListeningThread.")
