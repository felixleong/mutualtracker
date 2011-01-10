def rchop(string, ending):
    if string.endswith(ending):
        return(string[:-len(ending)])
    return string
