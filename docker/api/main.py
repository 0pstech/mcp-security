from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import secrets

app = FastAPI()

# Store issued tokens in memory (for demo purposes)
issued_tokens = set()

security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token not in issued_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing token",
            headers={"Authorization": "Bearer"},
        )
    return token


@app.post("/auth")
def auth():
    """Issue a random token."""
    token = secrets.token_urlsafe(32)
    issued_tokens.add(token)
    return {"token": token}


@app.get("/")
def get_data(token: str = Depends(verify_token)):
    """Return hardcoded data, requires valid token."""
    print('user is authenticated - token:', token)
    return {"message": "Here is your protected data!", "data": [1, 2, 3, 4, 5]}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
