def format_staging_dir(root, time, name):
    """Return directory used for staging of published assets

    TODO(marcus): Deprecated, this should be a path template similar to
        how other paths are defined.

    """

    dirname = os.path.join(root, "staging", name, time)
    return dirname
