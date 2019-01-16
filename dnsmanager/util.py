
def prompt_for_password(prompt):
    import getpass
    return getpass.getpass(
        prompt=prompt
    )
    
def prompt_y_n_question(question, default="no"):
    valid = {
        "yes": True, "y": True, "ye": True,
        "no": False, "n": False
    }
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("Invalid default answer: '{}'".format(default))

    while True:
        print(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please, respond with 'yes' or 'no' or 'y' or 'n'.")