from importlib import metadata

UNKNOWN_VERSION = 'unknown'


def distribution_version(distribution: str) -> str:
    """Look up an installed distribution's version without failing.

    Parameters
    ----------
    distribution : str
        Name of the distribution to look up, e.g. ``tzdata``.

    Returns
    -------
    str
        The installed version, or :data:`UNKNOWN_VERSION` when the
        distribution is not installed. A version string is informational,
        so a missing distribution reports ``unknown`` rather than raising:
        ``tzdata`` in particular is absent on systems that ship their own
        zoneinfo database, and the package itself is missing metadata when
        run straight from a source checkout.
    """
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return UNKNOWN_VERSION
