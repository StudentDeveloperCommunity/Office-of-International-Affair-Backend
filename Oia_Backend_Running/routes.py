from fastapi import APIRouter, HTTPException, Depends, status, Query, UploadFile, File, Form, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Union
import logging
import jwt
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
from models import (
    # v1 Models
    Program, ProgramCreate, ProgramUpdate,
    Contact, ContactCreate,
    AdminLogin, Stats,
    # v2.0 Models
    News, NewsCreate, NewsUpdate,
    Partnership, PartnershipCreate, PartnershipUpdate,
    TeamMember, TeamMemberCreate, TeamMemberUpdate,
    Event, EventCreate, EventUpdate,
    GalleryImage, GalleryImageCreate, GalleryImageUpdate,
    FAQ, FAQCreate, FAQUpdate,
    StaticContent, StaticContentCreate, StaticContentUpdate,
    ExtendedStats, PaginatedResponse, SearchResult,
    StatsConfig, StatsConfigUpdate,
    SuccessResponse, ErrorResponse
)
from database import DatabaseOperations

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'medicaps-exchange-programs-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Security scheme
security = HTTPBearer()

# Create router
router = APIRouter(prefix="/api")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return username"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Active admin sessions
active_admin_sessions = set()

# ========================
# PUBLIC ROUTES
# ========================

@router.get("/")
async def cron_wakeup():
    """
    Endpoint to keep Render free instance awake.
    Ping this every 10-12 minutes using UptimeRobot or cron-job.org
    """
    logger.info("Cron wakeup ping received")
    return {
        "status": "ok",
        "message": "OIA Website API - Medi-Caps University",
        "version": "2.0",
        "timestamp": datetime.utcnow()
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OIA Website API v2.0"}

# ========================
# PROGRAMS ROUTES (v1 - Retained, Extended)
# ========================

@router.get("/programs", response_model=PaginatedResponse)
async def get_programs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """Get all active exchange programs with pagination"""
    try:
        result = await DatabaseOperations.get_programs(active_only=True, page=page, page_size=page_size)
        return result
    except Exception as e:
        logger.error(f"Error fetching programs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/programs/{program_id}", response_model=Program)
async def get_program_detail(program_id: str):
    """Get program details by ID"""
    try:
        program = await DatabaseOperations.get_program_by_id(program_id)
        if not program:
            raise HTTPException(status_code=404, detail="Program not found")
        return program
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching program: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# NEWS ROUTES (v2.0 NEW)
# ========================

@router.get("/news", response_model=PaginatedResponse)
async def get_news(
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    featured_only: bool = False
):
    """Get news articles with filtering and pagination"""
    try:
        result = await DatabaseOperations.get_news(category=category, page=page, page_size=page_size, featured_only=featured_only)
        return result
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/news/{news_id}", response_model=News)
async def get_news_detail(news_id: str):
    """Get news article details"""
    try:
        news = await DatabaseOperations.get_news_by_id(news_id)
        if not news:
            raise HTTPException(status_code=404, detail="News article not found")
        return news
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching news: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# PARTNERSHIPS ROUTES (v2.0 NEW)
# ========================

@router.get("/partnerships", response_model=PaginatedResponse)
async def get_partnerships(
    type: Optional[str] = None,
    country: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """Get partnerships with filtering"""
    try:
        result = await DatabaseOperations.get_partnerships(type=type, country=country, page=page, page_size=page_size)
        return result
    except Exception as e:
        logger.error(f"Error fetching partnerships: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/partnerships/{partnership_id}", response_model=Partnership)
async def get_partnership_detail(partnership_id: str):
    """Get partnership details"""
    try:
        partnership = await DatabaseOperations.get_partnership_by_id(partnership_id)
        if not partnership:
            raise HTTPException(status_code=404, detail="Partnership not found")
        return partnership
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching partnership: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# TEAM ROUTES (v2.0 NEW)
# ========================

@router.get("/team", response_model=List[TeamMember])
async def get_team():
    """Get all team members"""
    try:
        members = await DatabaseOperations.get_team_members()
        return members
    except Exception as e:
        logger.error(f"Error fetching team: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/team/{member_id}", response_model=TeamMember)
async def get_team_member_detail(member_id: str):
    """Get team member details"""
    try:
        member = await DatabaseOperations.get_team_member_by_id(member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Team member not found")
        return member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team member: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# EVENTS ROUTES (v2.0 NEW)
# ========================

@router.get("/events", response_model=PaginatedResponse)
async def get_events(
    type: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    upcoming_only: bool = False
):
    """Get events with filtering and pagination"""
    try:
        result = await DatabaseOperations.get_events(type=type, page=page, page_size=page_size, upcoming_only=upcoming_only)
        return result
    except Exception as e:
        logger.error(f"Error fetching events: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/events/{event_id}", response_model=Event)
async def get_event_detail(event_id: str):
    """Get event details"""
    try:
        event = await DatabaseOperations.get_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching event: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# GALLERY ROUTES (v2.0 NEW)
# ========================

@router.get("/gallery", response_model=PaginatedResponse)
async def get_gallery(
    category: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100)
):
    """Get gallery images with filtering"""
    try:
        result = await DatabaseOperations.get_gallery_images(category=category, page=page, page_size=page_size)
        return result
    except Exception as e:
        logger.error(f"Error fetching gallery: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/gallery/{image_id}", response_model=GalleryImage)
async def get_gallery_image_detail(image_id: str):
    """Get gallery image details"""
    try:
        image = await DatabaseOperations.get_gallery_image_by_id(image_id)
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        return image
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching image: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# FAQ ROUTES (v2.0 NEW)
# ========================

@router.get("/faqs", response_model=List[FAQ])
async def get_faqs(category: Optional[str] = None):
    """Get FAQs with optional category filter"""
    try:
        faqs = await DatabaseOperations.get_faqs(category=category)
        return faqs
    except Exception as e:
        logger.error(f"Error fetching FAQs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# STATIC CONTENT ROUTES (v2.0 NEW)
# ========================

@router.get("/static-content", response_model=List[StaticContent])
async def get_static_content(section: Optional[str] = None):
    """Get static content by section"""
    try:
        content = await DatabaseOperations.get_static_content(section=section)
        return content
    except Exception as e:
        logger.error(f"Error fetching static content: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/static-content/{key}", response_model=StaticContent)
async def get_static_content_by_key(key: str):
    """Get static content by key"""
    try:
        content = await DatabaseOperations.get_static_content_by_key(key)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        return content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching static content: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# SEARCH ROUTES (v2.0 NEW)
# ========================

@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2),
    sections: Optional[str] = None
):
    """Global search across multiple collections"""
    try:
        section_list = sections.split(',') if sections else None
        results = await DatabaseOperations.global_search(q, section_list)
        return results
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ========================
# STATS ROUTES (Extended for v2.0)
# ========================

@router.get("/stats", response_model=Stats)
async def get_stats():
    """Get basic website statistics"""
    try:
        stats = await DatabaseOperations.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats/extended", response_model=ExtendedStats)
async def get_extended_stats():
    """Get extended statistics (v2.0)"""
    try:
        stats = await DatabaseOperations.get_extended_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching extended stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/admin/stats-config", response_model=StatsConfig)
async def get_stats_config_admin(current_username: str = Depends(verify_token)):
    """Get stats configuration - Admin only"""
    try:
        config = await DatabaseOperations.get_stats_config()
        return config
    except Exception as e:
        logger.error(f"Error fetching stats config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats config")


@router.put("/admin/stats-config", response_model=StatsConfig)
async def update_stats_config_admin(payload: StatsConfigUpdate, current_username: str = Depends(verify_token)):
    """Update stats configuration - Admin only"""
    try:
        update_data = {k: v for k, v in payload.dict().items() if v is not None}
        config = await DatabaseOperations.update_stats_config(update_data)
        return config
    except Exception as e:
        logger.error(f"Error updating stats config: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update stats config")

# ========================
# CONTACT/FORMS ROUTES (Extended for v2.0)
# ========================

@router.post("/contact", response_model=SuccessResponse)
async def submit_contact(contact: ContactCreate):
    """Submit contact/form submission"""
    try:
        await DatabaseOperations.create_contact(contact.dict())
        return SuccessResponse(message="Thank you for your message! We will get back to you within 24 hours.")
    except Exception as e:
        logger.error(f"Error submitting contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit form")

@router.post("/forms/{form_type}", response_model=SuccessResponse)
async def submit_typed_form(form_type: str, contact: ContactCreate):
    """Submit typed form (proposal, LOR, application, etc.)"""
    try:
        contact_dict = contact.dict()
        contact_dict['formType'] = form_type
        await DatabaseOperations.create_contact(contact_dict)
        
        form_messages = {
            'Proposal': 'Your proposal has been submitted successfully. Our team will review and contact you soon.',
            'LOR Request': 'Your LOR request has been received. We will process it within 5 business days.',
            'Application': 'Your application has been submitted. Check your email for further instructions.',
            'Partnership': 'Thank you for your interest in partnering with us. We will respond within 2 weeks.'
        }
        
        message = form_messages.get(form_type, 'Your submission has been received successfully.')
        return SuccessResponse(message=message)
    except Exception as e:
        logger.error(f"Error submitting form: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit form")

# ========================
# ADMIN AUTHENTICATION ROUTES
# ========================

@router.post("/admin/login")
async def admin_login(credentials: AdminLogin):
    """Admin login with JWT token generation"""
    try:
        is_authenticated = await DatabaseOperations.authenticate_admin(
            credentials.username, 
            credentials.password
        )
        
        if is_authenticated:
            access_token = create_access_token(data={"sub": credentials.username})
            active_admin_sessions.add(credentials.username)
            return {
                "success": True, 
                "message": "Login successful", 
                "username": credentials.username,
                "access_token": access_token,
                "token_type": "bearer"
            }
        else:
            return {"success": False, "message": "Invalid credentials"}
    except Exception as e:
        logger.error(f"Error during admin login: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/logout")
async def admin_logout(current_username: str = Depends(verify_token)):
    """Admin logout"""
    active_admin_sessions.discard(current_username)
    return SuccessResponse(message="Logged out successfully")

# ========================
# ADMIN PROGRAMS ROUTES (v1 - Retained)
# ========================

@router.get("/admin/programs", response_model=PaginatedResponse)
async def get_all_programs_admin(
    current_username: str = Depends(verify_token),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """Get all programs (including inactive) - Admin only"""
    try:
        result = await DatabaseOperations.get_programs(active_only=False, page=page, page_size=page_size)
        return result
    except Exception as e:
        logger.error(f"Error fetching admin programs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/admin/programs", response_model=Program)
async def create_program_admin(program: ProgramCreate, current_username: str = Depends(verify_token)):
    """Create new program - Admin only"""
    try:
        created_program = await DatabaseOperations.create_program(program.dict())
        return created_program
    except Exception as e:
        logger.error(f"Error creating program: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create program")

@router.put("/admin/programs/{program_id}", response_model=Program)
async def update_program_admin(program_id: str, program: ProgramUpdate, current_username: str = Depends(verify_token)):
    """Update program - Admin only"""
    try:
        update_data = {k: v for k, v in program.dict().items() if v is not None}
        updated_program = await DatabaseOperations.update_program(program_id, update_data)
        if not updated_program:
            raise HTTPException(status_code=404, detail="Program not found")
        return updated_program
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating program: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update program")

@router.delete("/admin/programs/{program_id}")
async def delete_program_admin(program_id: str, current_username: str = Depends(verify_token)):
    """Delete program - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_program(program_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Program not found")
        return SuccessResponse(message="Program deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting program: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete program")

# ========================
# ADMIN NEWS ROUTES (v2.0 NEW)
# ========================

@router.post("/admin/news", response_model=News)
async def create_news_admin(news: NewsCreate, current_username: str = Depends(verify_token)):
    """Create news article - Admin only"""
    try:
        created_news = await DatabaseOperations.create_news(news.dict())
        return created_news
    except Exception as e:
        logger.error(f"Error creating news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create news")

@router.put("/admin/news/{news_id}", response_model=News)
async def update_news_admin(news_id: str, news: NewsUpdate, current_username: str = Depends(verify_token)):
    """Update news article - Admin only"""
    try:
        update_data = {}
        news_dict = news.dict()
        
        # Only include fields that are not None and not empty strings
        for k, v in news_dict.items():
            if v is not None and (isinstance(v, str) and v.strip() != '' or not isinstance(v, str)):
                update_data[k] = v
        
        updated_news = await DatabaseOperations.update_news(news_id, update_data)
        if not updated_news:
            raise HTTPException(status_code=404, detail="News not found")
        return updated_news
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update news")

@router.delete("/admin/news/{news_id}")
async def delete_news_admin(news_id: str, current_username: str = Depends(verify_token)):
    """Delete news article - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_news(news_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="News not found")
        return SuccessResponse(message="News deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting news: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete news")

# ========================
# ADMIN PARTNERSHIPS ROUTES (v2.0 NEW)
# ========================

@router.post("/admin/partnerships", response_model=Partnership)
async def create_partnership_admin(partnership: PartnershipCreate, current_username: str = Depends(verify_token)):
    """Create partnership - Admin only"""
    try:
        created_partnership = await DatabaseOperations.create_partnership(partnership.dict())
        return created_partnership
    except Exception as e:
        logger.error(f"Error creating partnership: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create partnership")

@router.put("/admin/partnerships/{partnership_id}", response_model=Partnership)
async def update_partnership_admin(partnership_id: str, partnership: PartnershipUpdate, current_username: str = Depends(verify_token)):
    """Update partnership - Admin only"""
    try:
        update_data = {k: v for k, v in partnership.dict().items() if v is not None}
        updated_partnership = await DatabaseOperations.update_partnership(partnership_id, update_data)
        if not updated_partnership:
            raise HTTPException(status_code=404, detail="Partnership not found")
        return updated_partnership
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating partnership: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update partnership")

@router.delete("/admin/partnerships/{partnership_id}")
async def delete_partnership_admin(partnership_id: str, current_username: str = Depends(verify_token)):
    """Delete partnership - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_partnership(partnership_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Partnership not found")
        return SuccessResponse(message="Partnership deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting partnership: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete partnership")

# ========================
# ADMIN TEAM ROUTES (v2.0 NEW)
# ========================

@router.post("/admin/team", response_model=TeamMember)
async def create_team_member_admin(
    file: UploadFile = File(None),
    name: str = Form(...),
    role: str = Form(...),
    bio: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    department: str = Form(""),
    image_url: str = Form(None),
    order: int = Form(0),
    is_leadership: bool = Form(False),
    is_active: bool = Form(True),
    current_username: str = Depends(verify_token)
):
    """Create team member with optional file upload - Admin only"""
    try:
        # Handle image upload
        image_path = None
        if file:
            # Validate file type
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if file.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
            
            # Save the uploaded file
            image_path = save_team_upload_file(file)
        elif image_url:
            image_path = image_url
        
        # Prepare team member data
        member_data = {
            "name": name,
            "role": role,
            "bio": bio,
            "email": email,
            "phone": phone,
            "department": department,
            "image": f"/{image_path}" if image_path else None,
            "order": order,
            "is_leadership": is_leadership,
            "is_active": is_active,
            "uploadDate": datetime.utcnow()
        }
        
        # Save to database
        created_member = await DatabaseOperations.create_team_member(member_data)
        return created_member
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating team member: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create team member")

@router.put("/admin/team/{member_id}", response_model=TeamMember)
async def update_team_member_admin(
    member_id: str,
    request: Request,
    file: UploadFile = File(None),
    name: str = Form(None),
    role: str = Form(None),
    bio: str = Form(None),
    email: str = Form(None),
    phone: str = Form(None),
    department: str = Form(None),
    image_url: Optional[str] = Form(None),
    order: int = Form(None),
    is_leadership: bool = Form(None),
    is_active: bool = Form(None),
    current_username: str = Depends(verify_token)
):
    """Update team member - Admin only"""
    try:
        logger.info(f"=== TEAM MEMBER UPDATE DEBUG ===")
        logger.info(f"Member ID: {member_id}")
        logger.info(f"Received image_url parameter: '{image_url}' (type: {type(image_url)})")
        logger.info(f"image_url is None: {image_url is None}")
        logger.info(f"image_url length: {len(image_url) if image_url else 'N/A'}")
        
        # Debug all received parameters
        logger.info(f"All received parameters:")
        logger.info(f"  name: {name} (type: {type(name)})")
        logger.info(f"  role: {role} (type: {type(role)})")
        logger.info(f"  bio: {bio} (type: {type(bio)})")
        logger.info(f"  email: {email} (type: {type(email)})")
        logger.info(f"  phone: {phone} (type: {type(phone)})")
        logger.info(f"  department: {department} (type: {type(department)})")
        logger.info(f"  order: {order} (type: {type(order)})")
        logger.info(f"  is_leadership: {is_leadership} (type: {type(is_leadership)})")
        logger.info(f"  is_active: {is_active} (type: {type(is_active)})")
        
        existing = await DatabaseOperations.get_team_member_by_id(member_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Team member not found")

        # Handle image upload or URL
        update_data = {}
        
        if file:
            logger.info("Processing uploaded file...")
            # Validate file type
            if not file.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
            
            # Save the uploaded file
            image_path = save_team_upload_file(file)
            update_data['image'] = f"/{image_path}"
            logger.info(f"Image file uploaded: {image_path}")
        elif image_url is not None:
            # Handle image URL (including empty string for removal)
            logger.info(f"Processing image_url: '{image_url}' (length: {len(image_url)})")
            if image_url.strip() != '':
                update_data['image'] = f"/{image_url}"
                logger.info(f"Image URL updated: {image_url}")
            else:
                # Empty string means remove the image
                # First, get the current member to find the existing image file
                current_member = await DatabaseOperations.get_team_member_by_id(member_id)
                if current_member and current_member.get('image'):
                    old_image_path = current_member['image']
                    # Remove leading slash if present
                    if old_image_path.startswith('/'):
                        old_image_path = old_image_path[1:]
                    
                    # Construct full file path
                    full_file_path = old_image_path
                    
                    # Delete the actual image file
                    try:
                        if os.path.exists(full_file_path):
                            os.remove(full_file_path)
                            logger.info(f"Deleted image file: {full_file_path}")
                        else:
                            logger.info(f"Image file not found for deletion: {full_file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting image file {full_file_path}: {str(e)}")
                
                # Set image field to empty string in database
                update_data['image'] = ''
                logger.info("Image removal requested - setting image to empty string")
        else:
            logger.info("No image changes requested - image_url is None")
        
        # Check raw form data for image_url parameter
        try:
            form_data = await request.form()
            if 'image_url' in form_data:
                raw_image_url = form_data['image_url']
                logger.info(f"Raw form data image_url: '{raw_image_url}' (type: {type(raw_image_url)})")
                if raw_image_url == '' or raw_image_url == b'':
                    logger.info("Detected empty image_url in raw form data - processing removal")
                    # Empty string means remove the image
                    current_member = await DatabaseOperations.get_team_member_by_id(member_id)
                    if current_member and current_member.get('image'):
                        old_image_path = current_member['image']
                        # Remove leading slash if present
                        if old_image_path.startswith('/'):
                            old_image_path = old_image_path[1:]
                        
                        # Construct full file path
                        full_file_path = old_image_path
                        
                        # Delete the actual image file
                        try:
                            if os.path.exists(full_file_path):
                                os.remove(full_file_path)
                                logger.info(f"Deleted image file: {full_file_path}")
                            else:
                                logger.info(f"Image file not found for deletion: {full_file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting image file {full_file_path}: {str(e)}")
                    
                    # Set image field to empty string in database
                    update_data['image'] = ''
                    logger.info("Image removal processed from raw form data")
        except Exception as e:
            logger.error(f"Error reading raw form data: {str(e)}")
        
        logger.info(f"Final update_data image field: {update_data.get('image', 'NOT_SET')}")
        logger.info(f"=== END TEAM MEMBER UPDATE DEBUG ===")
        
        # Update other fields if provided
        logger.info(f"Processing boolean fields - is_leadership: {is_leadership}, is_active: {is_active}")
        if name is not None:
            update_data['name'] = name
        if role is not None:
            update_data['role'] = role
        if bio is not None:
            update_data['bio'] = bio
        if email is not None and email.strip() != '':
            update_data['email'] = email
        if phone is not None and phone.strip() != '':
            update_data['phone'] = phone
        if department is not None and department.strip() != '':
            update_data['department'] = department
        if order is not None:
            update_data['order'] = order
        if is_leadership is not None:
            update_data['is_leadership'] = is_leadership
            logger.info(f"Updated is_leadership to: {is_leadership}")
        if is_active is not None:
            update_data['is_active'] = is_active
            logger.info(f"Updated is_active to: {is_active}")
        
        logger.info(f"Final update_data: {update_data}")

        updated = await DatabaseOperations.update_team_member(member_id, update_data)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating team member: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update team member")

@router.delete("/admin/team/{member_id}")
async def delete_team_member_admin(member_id: str, current_username: str = Depends(verify_token)):
    """Delete team member - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_team_member(member_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Team member not found")
        return SuccessResponse(message="Team member deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting team member: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete team member")

# ========================
# ADMIN EVENTS ROUTES (v2.0 NEW)
# ========================

@router.post("/admin/events", response_model=Event)
async def create_event_admin(event: EventCreate, current_username: str = Depends(verify_token)):
    """Create event - Admin only"""
    try:
        created_event = await DatabaseOperations.create_event(event.dict())
        return created_event
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create event")

@router.put("/admin/events/{event_id}", response_model=Event)
async def update_event_admin(event_id: str, event: EventUpdate, current_username: str = Depends(verify_token)):
    """Update event - Admin only"""
    try:
        update_data = {}
        event_dict = event.dict()
        
        # Only include fields that are not None and not empty strings
        for k, v in event_dict.items():
            if v is not None and (isinstance(v, str) and v.strip() != '' or not isinstance(v, str)):
                update_data[k] = v
        
        updated_event = await DatabaseOperations.update_event(event_id, update_data)
        if not updated_event:
            raise HTTPException(status_code=404, detail="Event not found")
        return updated_event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update event")

@router.delete("/admin/events/{event_id}")
async def delete_event_admin(event_id: str, current_username: str = Depends(verify_token)):
    """Delete event - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_event(event_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Event not found")
        return SuccessResponse(message="Event deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete event")
# ADMIN GALLERY ROUTES (v2.0 NEW)
# ========================

# Create uploads directory if it doesn't exist
from pathlib import Path
import uuid
import shutil

UPLOAD_DIR = Path("uploads/gallery")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Create team uploads directory
TEAM_UPLOAD_DIR = Path("uploads/team")
TEAM_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(file: UploadFile, destination: Path) -> str:
    """Save uploaded file to the specified directory"""
    try:
        # Generate a unique filename
        file_ext = Path(file.filename).suffix
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = destination / file_name
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return str(file_path.relative_to("uploads"))
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file")

def save_team_upload_file(file: UploadFile) -> str:
    """Save uploaded team member profile picture"""
    return save_upload_file(file, TEAM_UPLOAD_DIR)

@router.post("/admin/gallery", response_model=GalleryImage)
async def upload_gallery_image_admin(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    category: str = Form(...),
    order: int = Form(0),
    is_featured: bool = Form(False),
    is_active: bool = Form(True),
    current_username: str = Depends(verify_token)
):
    """Upload gallery image - Admin only"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
        
        # Save the uploaded file
        file_path = save_upload_file(file, UPLOAD_DIR)
        
        # Prepare image data for database
        image_data = {
            "title": title,
            "description": description,
            "image": f"/{file_path}",
            "alt": title,
            "category": category,
            "order": order,
            "is_featured": is_featured,
            "is_active": is_active,
            "uploadDate": datetime.utcnow()
        }
        
        # Save to database
        result = await DatabaseOperations.create_gallery_image(image_data)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

@router.delete("/admin/gallery/{image_id}")
async def delete_gallery_image_admin(image_id: str, current_username: str = Depends(verify_token)):
    """Delete gallery image - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_gallery_image(image_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Image not found")
        return SuccessResponse(message="Image deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete image")


@router.put("/admin/gallery/{image_id}", response_model=GalleryImage)
async def update_gallery_image_admin(
    image_id: str,
    file: UploadFile = File(None),
    image_url: str = Form(None),
    title: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    order: int = Form(None),
    is_featured: bool = Form(None),
    is_active: bool = Form(None),
    current_username: str = Depends(verify_token)
):
    """Update gallery image - Admin only"""
    try:
        existing = await DatabaseOperations.get_gallery_image_by_id(image_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Image not found")

        update_data = {}

        # If a new file is provided, save it and overwrite the image path
        if file is not None:
            allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
            if file.content_type not in allowed_types:
                raise HTTPException(status_code=400, detail="Invalid file type. Only JPEG, PNG, GIF, and WebP are allowed.")
            file_path = save_upload_file(file, UPLOAD_DIR)
            update_data['image'] = f"/{file_path}"
            update_data['alt'] = title or existing.get('alt') or existing.get('title')
        elif image_url:
            update_data['image'] = image_url

        if title is not None:
            update_data['title'] = title
        if description is not None:
            update_data['description'] = description
        if category is not None:
            update_data['category'] = category
        if order is not None:
            update_data['order'] = order
        if is_featured is not None:
            update_data['is_featured'] = is_featured
        if is_active is not None:
            update_data['is_active'] = is_active

        updated = await DatabaseOperations.update_gallery_image(image_id, update_data)
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update image")

# ========================
# ADMIN FAQ ROUTES (v2.0 NEW)
# ========================

@router.post("/admin/faqs", response_model=FAQ)
async def create_faq_admin(faq: FAQCreate, current_username: str = Depends(verify_token)):
    """Create FAQ - Admin only"""
    try:
        created_faq = await DatabaseOperations.create_faq(faq.dict())
        return created_faq
    except Exception as e:
        logger.error(f"Error creating FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create FAQ")

@router.put("/admin/faqs/{faq_id}", response_model=FAQ)
async def update_faq_admin(faq_id: str, faq: FAQUpdate, current_username: str = Depends(verify_token)):
    """Update FAQ - Admin only"""
    try:
        update_data = {k: v for k, v in faq.dict().items() if v is not None}
        updated_faq = await DatabaseOperations.update_faq(faq_id, update_data)
        if not updated_faq:
            raise HTTPException(status_code=404, detail="FAQ not found")
        return updated_faq
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update FAQ")

@router.delete("/admin/faqs/{faq_id}")
async def delete_faq_admin(faq_id: str, current_username: str = Depends(verify_token)):
    """Delete FAQ - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_faq(faq_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="FAQ not found")
        return SuccessResponse(message="FAQ deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting FAQ: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete FAQ")

# ========================
# ADMIN STATIC CONTENT ROUTES (v2.0 NEW)
# ========================

@router.post("/admin/static-content", response_model=StaticContent)
async def create_static_content_admin(content: StaticContentCreate, current_username: str = Depends(verify_token)):
    """Create static content - Admin only"""
    try:
        created_content = await DatabaseOperations.create_static_content(content.dict())
        return created_content
    except Exception as e:
        logger.error(f"Error creating content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create content")

@router.put("/admin/static-content/{key}", response_model=StaticContent)
async def update_static_content_admin(key: str, content: StaticContentUpdate, current_username: str = Depends(verify_token)):
    """Update static content - Admin only"""
    try:
        update_data = {k: v for k, v in content.dict().items() if v is not None}
        updated_content = await DatabaseOperations.update_static_content(key, update_data)
        if not updated_content:
            raise HTTPException(status_code=404, detail="Content not found")
        return updated_content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update content")

@router.delete("/admin/static-content/{key}")
async def delete_static_content_admin(key: str, current_username: str = Depends(verify_token)):
    """Delete static content - Admin only"""
    try:
        deleted = await DatabaseOperations.delete_static_content(key)
        if not deleted:
            raise HTTPException(status_code=404, detail="Content not found")
        return SuccessResponse(message="Content deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting content: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete content")

# ========================
# ADMIN CONTACTS ROUTES (v1 - Retained, Extended)
# ========================

@router.get("/admin/contacts", response_model=List[Contact])
async def get_contacts_admin(
    current_username: str = Depends(verify_token),
    form_type: Optional[str] = None
):
    """Get all contact submissions - Admin only"""
    try:
        contacts = await DatabaseOperations.get_contacts(form_type=form_type)
        return contacts
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/admin/contacts/{contact_id}/read")
async def mark_contact_as_read(contact_id: str, current_username: str = Depends(verify_token)):
    """Mark contact message as read - Admin only"""
    try:
        success = await DatabaseOperations.update_contact_status(contact_id, "Read")
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"message": "Contact marked as read"}
    except Exception as e:
        logger.error(f"Error marking contact as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update contact status")

@router.delete("/admin/contacts/{contact_id}")
async def delete_contact_admin(contact_id: str, current_username: str = Depends(verify_token)):
    """Delete contact message - Admin only"""
    try:
        success = await DatabaseOperations.delete_contact(contact_id)
        if not success:
            raise HTTPException(status_code=404, detail="Contact not found")
        return {"message": "Contact deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete contact")
