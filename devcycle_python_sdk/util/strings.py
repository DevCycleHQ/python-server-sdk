def slash_join(*args) -> str:
    """
    Assembles a string, concatenating the arguments with a single slash between them
    removing any leading or trailing slashes from the arguments
    """
    return "/".join(str(arg).strip("/") for arg in args)
