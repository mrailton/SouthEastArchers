# Third-Party Library Warning Fix

## Issue

The `sumup` package (version 0.0.13) has a SyntaxWarning in its code.

## Solution Applied

Added warning suppression at the entry points to keep logs clean:

- **web.py** - Main Flask application
- **worker.py** - Background worker
- **manage.py** - Management CLI

```python
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
```

This suppresses the warning from third-party libraries while keeping your own code warnings visible.
