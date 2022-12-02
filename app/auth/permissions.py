from fastapi import Depends
from fastapi_permissions import (
    Authenticated,
    Everyone, configure_permissions)

from app.auth.dependecies import TokenData, get_current_user


def get_active_principals(user: TokenData = Depends(get_current_user)):
    if user:
        principals = [Everyone, Authenticated]
        principals.extend(user.principals)
        print(principals)
    else:
        principals = [Everyone]
    return principals


Permission = configure_permissions(get_active_principals)
