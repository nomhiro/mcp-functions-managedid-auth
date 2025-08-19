import jwt
import requests
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import azure.functions as func

class ManagedIdAuthenticator:
    """
    Authenticates Azure Managed Identity tokens
    """
    
    def __init__(self):
        self.jwks_uri = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
        self.issuer_base = "https://sts.windows.net/"
        self.audience = os.getenv("AZURE_CLIENT_ID", "https://management.azure.com/")
        self._jwks_cache = {}
        self._cache_expiry = None
    
    async def validate_token(self, request: func.HttpRequest) -> Optional[Dict[str, Any]]:
        """
        Validate the Bearer token from the request
        """
        try:
            # Extract Bearer token
            auth_header = request.headers.get('authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logging.warning("No Bearer token found in request")
                return None
            
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            # Decode token header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            if not kid:
                logging.error("Token missing key ID")
                return None
            
            # Get signing key
            signing_key = await self._get_signing_key(kid)
            if not signing_key:
                logging.error("Could not get signing key")
                return None
            
            # Verify token
            decoded_token = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.audience,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_iat": True
                }
            )
            
            # Additional validation
            if not self._validate_issuer(decoded_token.get('iss')):
                logging.error(f"Invalid issuer: {decoded_token.get('iss')}")
                return None
            
            logging.info(f"Token validated for subject: {decoded_token.get('sub')}")
            return decoded_token
            
        except jwt.ExpiredSignatureError:
            logging.error("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logging.error(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Token validation failed: {str(e)}")
            return None
    
    async def _get_signing_key(self, kid: str) -> Optional[str]:
        """
        Get signing key from JWKS endpoint
        """
        try:
            # Check cache first
            current_time = datetime.utcnow()
            if (self._cache_expiry and current_time < self._cache_expiry and 
                kid in self._jwks_cache):
                return self._jwks_cache[kid]
            
            # Fetch JWKS
            response = requests.get(self.jwks_uri, timeout=10)
            response.raise_for_status()
            
            jwks = response.json()
            
            # Find the key
            for key in jwks.get('keys', []):
                if key.get('kid') == kid:
                    # Convert to PEM format
                    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                    pem_key = public_key.public_key().public_bytes(
                        encoding=jwt.serialization.Encoding.PEM,
                        format=jwt.serialization.PublicFormat.SubjectPublicKeyInfo
                    ).decode('utf-8')
                    
                    # Cache the key
                    self._jwks_cache[kid] = pem_key
                    self._cache_expiry = current_time.replace(minute=current_time.minute + 10)
                    
                    return pem_key
            
            logging.error(f"Key ID {kid} not found in JWKS")
            return None
            
        except Exception as e:
            logging.error(f"Error fetching signing key: {str(e)}")
            return None
    
    def _validate_issuer(self, issuer: str) -> bool:
        """
        Validate token issuer
        """
        if not issuer:
            return False
        
        valid_issuers = [
            "https://sts.windows.net/",
            "https://login.microsoftonline.com/"
        ]
        
        return any(issuer.startswith(valid) for valid in valid_issuers)
    
    async def authorize(self, request: func.HttpRequest) -> Dict[str, Any]:
        """
        Authorize request and return authorization result
        """
        try:
            principal = await self.validate_token(request)
            
            if not principal:
                return {"authorized": False}
            
            # Additional authorization checks can be added here
            # For example, check roles, permissions, etc.
            
            return {
                "authorized": True,
                "principal": principal
            }
            
        except Exception as e:
            logging.error(f"Authorization failed: {str(e)}")
            return {"authorized": False, "error": str(e)}