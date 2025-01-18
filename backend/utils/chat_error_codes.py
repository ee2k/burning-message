from enum import Enum, auto

class ChatErrorCodes(str, Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name
    
    # Room creation/validation
    INVALID_ROOM_ID = auto()
    ROOM_ID_EXISTS = auto()
    INVALID_TOKEN = auto()
    ROOM_NOT_FOUND = auto()
    ROOM_FULL = auto()
    ROOM_EXPIRED = auto()
    
    # Participant management
    USER_NOT_FOUND = auto()
    INVALID_USERNAME = auto()
    
    # General
    SERVER_ERROR = auto()
    MEMORY_LIMIT = auto()

# HTTP status codes mapping
STATUS_CODES = {
    # Validation errors -> 400
    ChatErrorCodes.INVALID_ROOM_ID: 400,
    ChatErrorCodes.ROOM_ID_EXISTS: 400,
    ChatErrorCodes.INVALID_TOKEN: 400,
    ChatErrorCodes.INVALID_USERNAME: 400,
    
    # Not found -> 404
    ChatErrorCodes.ROOM_NOT_FOUND: 404,
    ChatErrorCodes.USER_NOT_FOUND: 404,
    
    # Resource limits -> 403
    ChatErrorCodes.ROOM_FULL: 403,
    ChatErrorCodes.ROOM_EXPIRED: 403,
    
    # Server errors -> 500, 507
    ChatErrorCodes.SERVER_ERROR: 500,
    ChatErrorCodes.MEMORY_LIMIT: 507,
}
