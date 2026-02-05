import gazu

def get_current_user():
    """
    Get currently logged in user.
    """
    return gazu.client.get_current_user()

def get_user_by_email(email):
    return gazu.person.get_person_by_email(email)
