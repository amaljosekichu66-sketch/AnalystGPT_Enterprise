"""
Enterprise Identity & Access Management Package for AnalystGPT Enterprise.
"""

from src.identity.context import (
    UserContext,
    get_current_user_context,
    set_current_user_context,
)
from src.identity.exceptions import (
    AuthenticationError,
    AuthorizationError,
    IdentityError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
    UserAlreadyExistsError,
    UserDisabledError,
    UserNotFoundError,
)
from src.identity.in_memory_user_repository import (
    InMemoryUserRepository,
)
from src.identity.interfaces import (
    IAuthenticator,
    IAuthorizationService,
    IPasswordHasher,
    ITokenRevocationService,
    ITokenService,
    IUserRepository,
)
from src.identity.models import (
    LogoutResponse,
    TokenResponse,
    User,
    UserCreate,
    UserLogin,
    UserResponse,
    UserRole,
    UserStatus,
    UserUpdate,
)
from src.identity.password_hasher import (
    PBKDF2PasswordHasher,
)
from src.identity.permissions import (
    Permission,
    get_role_permissions,
    has_permission,
)
from src.identity.token_revocation import (
    TokenRevocationService,
)
from src.identity.token_service import (
    TokenService,
)
from src.identity.user_service import (
    UserService,
)

__all__ = [
    "UserRole",
    "UserStatus",
    "User",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "TokenResponse",
    "LogoutResponse",
    "Permission",
    "get_role_permissions",
    "has_permission",
    "UserContext",
    "get_current_user_context",
    "set_current_user_context",
    "IPasswordHasher",
    "IUserRepository",
    "IAuthenticator",
    "IAuthorizationService",
    "ITokenService",
    "ITokenRevocationService",
    "PBKDF2PasswordHasher",
    "InMemoryUserRepository",
    "TokenService",
    "TokenRevocationService",
    "UserService",
    "IdentityError",
    "AuthenticationError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "UserDisabledError",
    "AuthorizationError",
    "PermissionDeniedError",
]
