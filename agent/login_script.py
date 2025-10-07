from fastapi import HTTPException
import httpx
import jwt

BASE_URL = "https://api-test.penny.co/api/auth"
JWT_AUTH_SECRET = "58dd47041c191ed7fd1376862ca798384d36aa450cf8dcc1199d099467427b82"

async def login_user(email: str, password: str) -> str:
    """
    Logs in the user and returns the access token.
    """
    url = f"{BASE_URL}/login"
    payload = {
        "email": email,
        "password": password,
        "platform": "web"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)

    try:
        data = response.json()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid JSON response: {response.text}")

    access_token = data.get("accessToken")
    if not access_token:
        raise HTTPException(status_code=400, detail=f"Login failed: {response.text}")

    return access_token


def decode_jwt_token(token: str) -> dict:
    """
    Decodes the JWT token and extracts user and org info.
    """
    try:
        decoded_payload = jwt.decode(token, JWT_AUTH_SECRET, algorithms=["HS256"], leeway=30)
        user_info = decoded_payload.get("user", {})
        user_id = user_info.get("info", {}).get("id")
        org_code = user_info.get("orgInfo", {}).get("code")

        if not user_id or not org_code:
            raise HTTPException(status_code=400, detail="Failed to extract user ID or org code from token")

        return {"user_id": user_id, "org_code": org_code}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
# email = 'prottoitruyessa-2789@yopmail.com'
# password = 'Demo@2022'

# if __name__ == "__main__":
#     token = asyncio.run(login_user(email, password))
#     print(decode_jwt_token(token=token))