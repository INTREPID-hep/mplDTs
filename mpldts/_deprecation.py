"""2.9 says what 3.0 removes (T-074, `.agents/migration-3.0.md`).

2.x keeps the pre-refactor API alive so the downstream packages could migrate
one step at a time (ADR-025). This is the module that makes the exit visible:
every message names what to call instead, so a consumer moves one warning at a
time instead of reading a changelog. Nothing here changes behaviour, and the
list of what goes lives in the migration plan, not here.
"""

import warnings


def deprecated(old, new):
    """Warn that `old` goes away in 3.0 and that `new` does the same job."""
    warnings.warn(
        "%s goes away in mplDTs 3.0; use %s" % (old, new),
        DeprecationWarning,
        stacklevel=3,
    )
