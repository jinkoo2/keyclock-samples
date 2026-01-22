import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt
from jose.exceptions import JWTClaimsError
import requests

# -----------------------------
# Configuration
# -----------------------------
KEYCLOAK_URL = "http://localhost:8080"
REALM = "myrealm"
CLIENT_ID = "react-client"
ALGORITHMS = ["RS256"]

JWKS_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/certs"
ISSUER = f"{KEYCLOAK_URL}/realms/{REALM}"

# -----------------------------
# App setup
# -----------------------------
app = FastAPI()
security = HTTPBearer()
logger = logging.getLogger("auth")
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Load Keycloak public keys
# -----------------------------
jwks = requests.get(JWKS_URL).json()


# -----------------------------
# Helpers
# -----------------------------
def get_rsa_key(token: str):
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception:
        logger.warning("Failed to parse token header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header"
        )

    kid = unverified_header.get("kid")
    if not kid:
        logger.warning("Token missing kid")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    logger.info("Resolving JWK for kid=%s", kid)
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    logger.warning("No matching JWK for kid=%s", kid)
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# -----------------------------
# Auth dependency
# -----------------------------
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        rsa_key = get_rsa_key(token)
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer=ISSUER,
            )
        except JWTClaimsError:
            # Some tokens (e.g., public clients) may not carry the audience we expect; fallback to manual check.
            logger.info("JWT audience check failed, retrying without audience to inspect claims")
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                issuer=ISSUER,
                options={"verify_aud": False},
            )
            aud_claim = payload.get("aud")
            azp_claim = payload.get("azp")
            aud_ok = False
            if isinstance(aud_claim, list) and CLIENT_ID in aud_claim:
                aud_ok = True
            elif isinstance(aud_claim, str) and aud_claim == CLIENT_ID:
                aud_ok = True
            elif azp_claim == CLIENT_ID:
                aud_ok = True
            if not aud_ok:
                logger.warning(
                    "Invalid audience after fallback: aud=%s azp=%s expected=%s",
                    aud_claim,
                    azp_claim,
                    CLIENT_ID,
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid audience",
                )

        logger.info(
            "Token validated: sub=%s aud=%s",
            payload.get("sub"),
            payload.get("aud"),
        )
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )

    except Exception as exc:
        logger.exception("Token validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

# -----------------------------
# Role checker (optional)
# -----------------------------
def require_role(role: str):
    def checker(user=Depends(get_current_user)):
        roles = user.get("realm_access", {}).get("roles", [])
        if role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden",
            )
        return user

    return checker


# -----------------------------
# Routes
# -----------------------------
@app.get("/public")
def public():
    return {"message": "This is public"}


@app.get("/protected")
def protected(user=Depends(get_current_user)):
    return {
        "username": user.get("preferred_username"),
        "roles": user.get("realm_access", {}).get("roles", []),
    }


@app.get("/admin")
def admin(user=Depends(require_role("admin"))):
    return {"message": "Welcome admin"}
