"""
Asset management tools for HeyGen API (voices, avatars, avatar groups).
"""

from typing import Dict, Any, Optional
from .base import make_request

async def heygen_get_voices() -> Dict[str, Any]:
    """
    Retrieve a list of available voices from the HeyGen API.
    Limited to first 100 voices.
    
    Returns:
        Dict containing list of available voices
    """
    return await make_request("GET", "/v2/voices", params={"limit": 100})

async def heygen_get_voice_locales() -> Dict[str, Any]:
    """
    Retrieve a list of available voice locales (languages) from the HeyGen API.
    
    Returns:
        Dict containing list of available voice locales
    """
    return await make_request("GET", "/v2/voices/locales")

async def heygen_get_avatar_groups() -> Dict[str, Any]:
    """
    Retrieve a list of HeyGen avatar groups.
    
    Returns:
        Dict containing list of avatar groups
    """
    return await make_request("GET", "/v2/avatar_group.list")

async def heygen_get_avatars_in_avatar_group(group_id: str) -> Dict[str, Any]:
    """
    Retrieve a list of avatars in a specific HeyGen avatar group.
    
    Args:
        group_id: The ID of the avatar group
        
    Returns:
        Dict containing list of avatars in the specified group
    """
    return await make_request("GET", f"/v2/avatar_groups/{group_id}/avatars")

async def heygen_list_avatars() -> Dict[str, Any]:
    """
    Retrieve a list of all available avatars from the HeyGen API.
    This includes your instant avatars and public avatars.
    
    Returns:
        Dict containing list of all available avatars
    """
    return await make_request("GET", "/v2/avatars")