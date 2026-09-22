# TracePince

Desktop serial acquisition and live monitoring for Chauvin Arnoux Harmonic & Power Meter devices.

## Setup

The workspace is configured for `$HOME/.venvs/embedded/bin/python`.

```bash
python -m pip install -r requirements.txt
python main.py
```

## Build executables

On Windows, run `build_windows.bat` from the project directory. It creates:

```text
dist\TracePince.exe
```

On Fedora Sway Atomic or another Linux desktop, make the script executable
once and run it:

```bash
chmod +x build_linux.sh
./build_linux.sh
```

The Linux executable is created at:

```text
dist/TracePince
```

Both scripts create a separate `.venv-build` environment, install the project
dependencies and PyInstaller, and leave a `dist/logs` directory next to the
executable for raw serial logs. Build on the target operating system: a
Windows executable must be built on Windows, and a Linux executable on Linux.

On Linux, install the system Tk package before launching the GUI. For Debian/Ubuntu this is usually `python3-tk`; the package must match the Python interpreter used by the virtual environment. Matplotlib also requires a display unless the application is run under a desktop session.

The application creates one binary-preserving raw log under `logs/` per connection session. Parsed measurements are held separately in memory and are never written back over the raw data.

## Tests

```bash
python -m unittest discover -s tests -v
```