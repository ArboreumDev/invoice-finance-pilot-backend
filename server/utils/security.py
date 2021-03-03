from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def get_hashed_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(e)
        return False


# Authenticate username and password to give JWT token
def authenticate_user():
    pass

# Create access JWT token
def create_jwt_token():
    pass

# Check whether JWT token is correct
def check_jwt_token():
    pass

# Last checking and returning the final result
def final_checks(role: str):
    pass
