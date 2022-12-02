from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_permissions import All, Allow, Authenticated
from sqlalchemy.orm import Session

from app.auth.dependecies import authenticate_user, Token, create_access_token, get_current_active_user, \
    ACCESS_TOKEN_EXPIRE_MINUTES, TokenData
from app.auth.permissions import Permission
from app.constants import Roles
from app.database.database import get_db

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    token_data = TokenData(
        id=user.id,
        email=user.email,
        disabled=user.disabled,
        principals=[f"role:{Roles.map_id_to_name[user.id_role]}"]
    )

    access_token = create_access_token(
        data=token_data,
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", dependencies=[Permission("view", [(Allow, Authenticated, All)])])
async def read_users_me():
    return {}

