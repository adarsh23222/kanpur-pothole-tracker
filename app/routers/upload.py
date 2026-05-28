"""
routers/upload.py — Image Upload via Cloudinary
"""
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.models.user import User
from app.middleware.auth import get_current_user

# Configure Cloudinary
cloudinary.config(
    cloud_name = settings.CLOUDINARY_CLOUD_NAME,
    api_key    = settings.CLOUDINARY_API_KEY,
    api_secret = settings.CLOUDINARY_API_SECRET,
    secure     = True
)

router = APIRouter(prefix="/upload", tags=["Upload"])


class UploadResponse(BaseModel):
    url:       str
    public_id: str
    format:    str
    size:      int


@router.post("/image", response_model=UploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)  # Any logged in user
):
    """
    Upload image to Cloudinary.
    Accepts: JPG, PNG, GIF, WEBP
    Max size: 5MB
    Returns: permanent URL
    """

    # File type check
    ALLOWED = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in ALLOWED:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only JPG, PNG, GIF, and WEBP are allowed."
        )

    # File size check — 5MB max
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 5MB."
        )

    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            contents,
            folder       = "kanpur_pothole_tracker",
            resource_type= "image",
            quality      = "auto",   # Auto compress
            fetch_format = "auto",   # Auto best format
        )

        return UploadResponse(
            url       = result["secure_url"],
            public_id = result["public_id"],
            format    = result["format"],
            size      = result["bytes"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )
