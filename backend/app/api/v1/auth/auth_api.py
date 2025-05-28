from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from app.services.auth.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()

# --- Pydantic Schemas ---
class SignupRequest(BaseModel):
    full_name: constr(min_length=1)
    email: EmailStr
    password: constr(min_length=3)
    company_name: Optional[str] = None

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: constr(min_length=4, max_length=10)

class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=3)

class PasswordResetInitRequest(BaseModel):
    email: EmailStr

class PasswordResetRequest(BaseModel):
    email: EmailStr
    otp: constr(min_length=4, max_length=10)
    new_password: constr(min_length=3)

class DeleteAccountRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=3)

# --- API Endpoints ---

@router.post("/signup", summary="Start signup and send OTP")
def signup(data: SignupRequest):
    success, msg = auth_service.signup_user(
        data.full_name, data.email, data.password, data.company_name
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"detail": msg}

@router.post("/verify-otp", summary="Verify OTP to complete signup")
def verify_signup_otp(data: OTPVerifyRequest):
    success, msg = auth_service.verify_signup_otp(data.email, data.otp)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"detail": msg["message"], "user_id": msg["user_id"]}

@router.post("/login", summary="Login user")
def login(data: LoginRequest):
    success, msg = auth_service.login_user(data.email, data.password)
    if not success:
        raise HTTPException(status_code=401, detail=msg)
    return {"detail": msg["message"], "user_id": msg["user_id"]}

@router.post("/password-reset/initiate", summary="Initiate password reset (send OTP)")
def initiate_password_reset(data: PasswordResetInitRequest):
    success, msg = auth_service.initiate_password_reset(data.email)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"detail": msg}

@router.post("/password-reset/complete", summary="Complete password reset with OTP")
def complete_password_reset(data: PasswordResetRequest):
    success, msg = auth_service.reset_password(data.email, data.otp, data.new_password)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"detail": msg}

@router.post("/delete-account", summary="Delete user account (requires login)")
def delete_account(data: DeleteAccountRequest):
    # Authenticate user first
    success, msg = auth_service.login_user(data.email, data.password)
    if not success:
        raise HTTPException(status_code=401, detail=msg)
    user_id = msg["user_id"]
    success, msg = auth_service.delete_user_account(user_id)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"detail": msg}
