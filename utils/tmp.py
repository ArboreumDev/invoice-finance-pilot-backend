from passlib.context import CryptContext

# run this file with
# > python3 -m utils.tmp

pwd_context = CryptContext(schemes=["bcrypt"])


def get_hashed_password(password: str):
    return pwd_context.hash(password)


print(get_hashed_password("tusker"))
