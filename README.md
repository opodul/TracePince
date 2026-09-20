# TracePince

Desktop serial acquisition and live monitoring for Chauvin Arnoux Harmonic & Power Meter devices.

## Setup

The workspace is configured for `$HOME/.venvs/embedded/bin/python`.

```bash
python -m pip install -r requirements.txt
python main.py
```

On Linux, install the system Tk package before launching the GUI. For Debian/Ubuntu this is usually `python3-tk`; the package must match the Python interpreter used by the virtual environment. Matplotlib also requires a display unless the application is run under a desktop session.

The application creates one binary-preserving raw log under `logs/` per connection session. Parsed measurements are held separately in memory and are never written back over the raw data.

## Tests

```bash
python -m unittest discover -s tests -v
```