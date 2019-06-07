PAIRWISE_DRIVER_EXCEPTIONS = {
    'verstappen': 'max_verstappen',
    'magnussen': 'kevin_magnussen'
}


def initials_for_driver(name):
    new_name = ''
    if ((name) and (len(name) > 2)):
        new_name = name[0:3].upper()
    return new_name


def rename_drivers(name):
    new_name = name.lower()

    new_name = PAIRWISE_DRIVER_EXCEPTIONS.get(
        new_name, new_name)

    return new_name
