import lldb
from utils.DebugSessionListeningThread import DebugSessionListeningThread


def __lldb_init_module(debugger, internal_dict):
    """Initializes the LLDB session event listener."""
    listener_thread = DebugSessionListeningThread(debugger)
    listener_thread.start()
