# LLDB Logcat Integration

This tool integrates Android `adb logcat` with LLDB to provide real-time logging within the LLDB console. It is designed to work within Xcode and provides a seamless experience for debugging Android applications using LLDB. The main idea was born when the author played around with `SKIP.tool`, so some other environments or use cases may still require some "fine-tuning."

## Features

- **Real-time Logcat Integration**: Automatically starts and stops `adb logcat` based on the LLDB process state.
- **Log Filtering**: Filters logs based on the bundle ID of the target application.
- **TTY Redirection**: Logs are redirected to the LLDB console inside Xcode.
- **Automatic Cleanup**: Ensures that `adb logcat` is properly stopped and cleaned up when the debugging session ends.

## Usage

1. **Set Up the Environment**:
    Ensure that `adb` is installed and accessible from `lldb`. The default path is `/opt/homebrew/bin/adb`.

2. **Load the Script in LLDB**:
    - In your LLDB session:
    ```lldb
    command script import /path/to/lldb_logcat.py
    ```
    - or add this import to your `.lldbinit`.

3. **Start Debugging**:
    The tool will automatically start `adb logcat` and redirect logs to the LLDB console.

## File Structure

- [lldb_logcat.py](https://github.com/uixbuilder/logcat-to-lldb-logging/blob/main/lldb_logcat.py): Initializes the LLDB session event listener.
- [ActiveSessionLogger.py](https://github.com/uixbuilder/logcat-to-lldb-logging/blob/main/utils/ActiveSessionLogger.py): Handles logging to the LLDB console.
- [AndroidEmulatorObserverThread.py](https://github.com/uixbuilder/logcat-to-lldb-logging/blob/main/utils/AndroidEmulatorObserverThread.py): Manages the `adb logcat` subprocess.
- [DebugSessionListeningThread.py](https://github.com/uixbuilder/logcat-to-lldb-logging/blob/main/utils/DebugSessionListeningThread.py): Listens for LLDB process state changes and controls the `adb logcat` subprocess accordingly.

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/uixbuilder/logcat-to-lldb-logging/blob/main/LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgements

- [LLDB](https://lldb.llvm.org/)
- [Android Debug Bridge (adb)](https://developer.android.com/studio/command-line/adb)