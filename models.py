from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid

# ========================
# ENUMS
# ========================

class ProgramStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class ContactStatus(str, Enum):
    NEW = "New"
    READ = "Read"
    REPLIED = "Replied"

# v2.0 New Enums
class NewsCategory(str, Enum):
    ANNOUNCEMENT = "Announcement"
    MOU = "MoU"
    ACHIEVEMENT = "Achievement"
    PRESS = "Press Release"

class PartnershipType(str, Enum):
    STRATEGIC = "Strategic"
    RESEARCH = "Research"
    DUAL_DEGREE = "Dual Degree"
    STUDENT_EXCHANGE = "Student Exchange"

class PartnershipStatus(str, Enum):
    ACTIVE = "Active"
    UNDER_NEGOTIATION = "Under Negotiation"
    EXPIRED = "Expired"

class EventType(str, Enum):
    VISIT = "Visit"
    CONFERENCE = "Conference"
    SEMINAR = "Seminar"
    WEBINAR = "Webinar"
    DELEGATION = "Delegation"

class FormType(str, Enum):
    ENQUIRY = "Enquiry"
    PROPOSAL = "Proposal"
    LOR_REQUEST = "LOR Request"
    APPLICATION = "Application"
    PARTNERSHIP = "Partnership"

class GalleryCategory(str, Enum):
    EVENTS = "Events"
    CAMPUS = "Campus"
    PARTNERSHIPS = "Partnerships"
    CULTURAL = "Cultural"
    DELEGATIONS = "Delegations"

class FAQCategory(str, Enum):
    ADMISSIONS = "Admissions"
    MOBILITY = "Mobility"
    VISAS = "Visas"
    GENERAL = "General"
    PARTNERSHIPS = "Partnerships"
    
    @classmethod
    def _missing_(cls, value):
        # Handle case-insensitive matching
        value = str(value).title()
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        return None

# ========================
# PROGRAM MODELS (v1 - Retained)
# ========================

class ProgramBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    partnerUniversity: str = Field(..., min_length=1, max_length=200)
    duration: str = Field(..., min_length=1, max_length=100)
    eligibility: str = Field(..., min_length=1, max_length=500)
    deadline: str = Field(..., min_length=1, max_length=100)
    applicationLink: str = Field(..., min_length=1)
    image: Optional[str] = Field(None)
    status: ProgramStatus = Field(default=ProgramStatus.ACTIVE)
    
    # Enhanced Program Details
    purpose: Optional[str] = Field(None, max_length=1000)
    vision: Optional[str] = Field(None, max_length=500)
    benefits: Optional[List[str]] = Field(default_factory=list)
    eligibilityDetailed: Optional[List[str]] = Field(default_factory=list)
    tuitionFee: Optional[str] = Field(None, max_length=200)
    livingExpenses: Optional[str] = Field(None, max_length=200)
    insurance: Optional[str] = Field(None, max_length=200)
    visaFees: Optional[str] = Field(None, max_length=200)
    travel: Optional[str] = Field(None, max_length=200)
    scholarships: Optional[List[str]] = Field(default_factory=list)
    accommodation: Optional[List[str]] = Field(default_factory=list)
    
    # University Information
    universityFounded: Optional[str] = Field(None, max_length=100)
    universityRanking: Optional[str] = Field(None, max_length=200)
    universitySpecialties: Optional[List[str]] = Field(default_factory=list)
    campusInfo: Optional[str] = Field(None, max_length=200)
    studentBody: Optional[str] = Field(None, max_length=200)

    @validator('applicationLink')
    def validate_application_link(cls, v):
        if not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Application link must be a valid URL')
        return v

class ProgramCreate(ProgramBase):
    pass

class ProgramUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    partnerUniversity: Optional[str] = Field(None, min_length=1, max_length=200)
    duration: Optional[str] = Field(None, min_length=1, max_length=100)
    eligibility: Optional[str] = Field(None, min_length=1, max_length=500)
    deadline: Optional[str] = Field(None, min_length=1, max_length=100)
    applicationLink: Optional[str] = Field(None, min_length=1)
    image: Optional[str] = None
    status: Optional[ProgramStatus] = None
    purpose: Optional[str] = Field(None, max_length=1000)
    vision: Optional[str] = Field(None, max_length=500)
    benefits: Optional[List[str]] = None
    eligibilityDetailed: Optional[List[str]] = None
    tuitionFee: Optional[str] = Field(None, max_length=200)
    livingExpenses: Optional[str] = Field(None, max_length=200)
    insurance: Optional[str] = Field(None, max_length=200)
    visaFees: Optional[str] = Field(None, max_length=200)
    travel: Optional[str] = Field(None, max_length=200)
    scholarships: Optional[List[str]] = None
    accommodation: Optional[List[str]] = None
    universityFounded: Optional[str] = Field(None, max_length=100)
    universityRanking: Optional[str] = Field(None, max_length=200)
    universitySpecialties: Optional[List[str]] = None
    campusInfo: Optional[str] = Field(None, max_length=200)
    studentBody: Optional[str] = Field(None, max_length=200)

    @validator('applicationLink')
    def validate_application_link(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Application link must be a valid URL')
        return v

class Program(ProgramBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# NEWS MODELS (v2.0 NEW)
# ========================

class NewsBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=10, max_length=5000)
    category: NewsCategory
    date: datetime = Field(default_factory=datetime.utcnow)
    image: Optional[str] = None
    file: Optional[str] = None  # PDF document link
    author: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = Field(default_factory=list)
    featured: bool = Field(default=False)

class NewsCreate(NewsBase):
    pass

class NewsUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = Field(None, min_length=10, max_length=5000)
    category: Optional[NewsCategory] = None
    date: Optional[datetime] = None
    image: Optional[str] = None
    file: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100)
    tags: Optional[List[str]] = None
    featured: Optional[bool] = None

class News(NewsBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# PARTNERSHIP MODELS (v2.0 NEW)
# ========================

class PartnershipBase(BaseModel):
    partnerName: str = Field(..., min_length=1, max_length=300)
    type: PartnershipType
    country: str = Field(..., min_length=1, max_length=100)
    details: str = Field(..., min_length=10, max_length=2000)
    status: PartnershipStatus = Field(default=PartnershipStatus.ACTIVE)
    signedDate: Optional[datetime] = None
    expiryDate: Optional[datetime] = None
    document: Optional[str] = None  # MoU document
    logo: Optional[str] = None
    website: Optional[str] = None
    contactPerson: Optional[str] = Field(None, max_length=200)
    contactEmail: Optional[str] = Field(None, max_length=200)
    benefits: Optional[List[str]] = Field(default_factory=list)

    @validator('website')
    def validate_website(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Website must be a valid URL')
        return v

class PartnershipCreate(PartnershipBase):
    pass

class PartnershipUpdate(BaseModel):
    partnerName: Optional[str] = Field(None, min_length=1, max_length=300)
    type: Optional[PartnershipType] = None
    country: Optional[str] = Field(None, min_length=1, max_length=100)
    details: Optional[str] = Field(None, min_length=10, max_length=2000)
    status: Optional[PartnershipStatus] = None
    signedDate: Optional[datetime] = None
    expiryDate: Optional[datetime] = None
    document: Optional[str] = None
    logo: Optional[str] = None
    website: Optional[str] = None
    contactPerson: Optional[str] = Field(None, max_length=200)
    contactEmail: Optional[str] = Field(None, max_length=200)
    benefits: Optional[List[str]] = None

class Partnership(PartnershipBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# TEAM MODELS (v2.0 NEW)
# ========================

class TeamMemberBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=200)
    bio: str = Field(..., min_length=10, max_length=5000)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    department: Optional[str] = Field(None, max_length=200)
    office: Optional[str] = Field(None, max_length=200)
    image: Optional[str] = Field(None, max_length=500)
    responsibilities: Optional[List[str]] = Field(default_factory=list)
    order: int = Field(default=0)  # For sorting display order
    is_active: bool = Field(default=True)  # Add is_active field
    is_leadership: bool = Field(default=False)  # Add is_leadership field

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[str] = Field(None, min_length=1, max_length=200)
    bio: Optional[str] = Field(None, min_length=10, max_length=5000)
    department: Optional[str] = Field(None, min_length=1, max_length=200)
    image: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    office: Optional[str] = Field(None, max_length=100)
    responsibilities: Optional[List[str]] = None
    order: Optional[int] = None
    is_active: Optional[bool] = None  # Add is_active field for updates
    is_leadership: Optional[bool] = None  # Add is_leadership field for updates

class TeamMember(TeamMemberBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# EVENT MODELS (v2.0 NEW)
# ========================

class EventBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    type: EventType
    description: str = Field(..., min_length=10, max_length=2000)
    startDate: datetime
    endDate: Optional[datetime] = None
    venue: Optional[str] = Field(None, max_length=300)
    organizer: Optional[str] = Field(None, max_length=200)
    participants: Optional[List[str]] = Field(default_factory=list)
    images: Optional[List[str]] = Field(default_factory=list)
    featured: bool = Field(default=False)
    registrationLink: Optional[str] = None

    @validator('registrationLink')
    def validate_registration_link(cls, v):
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Registration link must be a valid URL')
        return v

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    type: Optional[EventType] = None
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    venue: Optional[str] = Field(None, max_length=300)
    organizer: Optional[str] = Field(None, max_length=200)
    participants: Optional[List[str]] = None
    images: Optional[List[str]] = None
    featured: Optional[bool] = None
    registrationLink: Optional[str] = None

class Event(EventBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# GALLERY MODELS (v2.0 NEW)
# ========================

class GalleryImageBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=1000)
    image: str = Field(..., min_length=1)  # URL to the image
    alt: Optional[str] = Field(None, max_length=200)
    category: str = Field(..., min_length=1)
    order: int = Field(default=0, ge=0)
    is_featured: bool = Field(default=False)
    is_active: bool = Field(default=True)
    tags: Optional[List[str]] = Field(default_factory=list)

class GalleryImageCreate(GalleryImageBase):
    pass

class GalleryImageUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    image: Optional[str] = None
    alt: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, min_length=1)
    order: Optional[int] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None

class GalleryImage(GalleryImageBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    uploadDate: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# FAQ MODELS (v2.0 NEW)
# ========================

class FAQBase(BaseModel):
    question: str = Field(..., min_length=5, max_length=500)
    answer: str = Field(..., min_length=10, max_length=2000)
    category: FAQCategory
    order: int = Field(default=0)
    featured: bool = Field(default=False)

class FAQCreate(FAQBase):
    pass

class FAQUpdate(BaseModel):
    question: Optional[str] = Field(None, min_length=5, max_length=500)
    answer: Optional[str] = Field(None, min_length=10, max_length=2000)
    category: Optional[FAQCategory] = None
    order: Optional[int] = None
    featured: Optional[bool] = None

class FAQ(FAQBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# CONTACT MODELS (Extended for v2.0)
# ========================

class ContactCreate(BaseModel):
    firstName: str = Field(..., min_length=1, max_length=100)
    lastName: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=1, max_length=200)
    phone: Optional[str] = Field(None, max_length=20)
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=10, max_length=2000)
    formType: FormType = Field(default=FormType.ENQUIRY)  # NEW for v2.0
    country: Optional[str] = Field(None, max_length=100)
    institution: Optional[str] = Field(None, max_length=200)

    @validator('email')
    def validate_email(cls, v):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v

class Contact(ContactCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: ContactStatus = Field(default=ContactStatus.NEW)
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# ADMIN MODELS (v1 - Retained)
# ========================

class AdminLogin(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=200)

class AdminUser(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(..., min_length=1, max_length=50)
    password: str  # This will be hashed
    role: str = Field(default="admin")
    createdAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# STATS MODELS (Extended for v2.0)
# ========================

class Stats(BaseModel):
    totalPrograms: int
    partnerUniversities: int
    studentsExchanged: int
    countries: int

class ExtendedStats(Stats):
    totalEvents: int
    activePartnerships: int
    internationalStudents: int
    newsArticles: int
    teamMembers: int


class StatsConfig(BaseModel):
    studentsExchanged: int


class StatsConfigUpdate(BaseModel):
    studentsExchanged: Optional[int] = Field(None, ge=0)

# ========================
# STATIC CONTENT MODELS (v2.0 NEW)
# For admin-editable static content
# ========================

class StaticContentBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)  # e.g., "vision_mission", "policies"
    title: str = Field(..., min_length=1, max_length=300)
    content: str = Field(..., min_length=10)  # Markdown or HTML
    section: str = Field(..., min_length=1, max_length=100)  # e.g., "about", "admissions"

class StaticContentCreate(StaticContentBase):
    pass

class StaticContentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = Field(None, min_length=10)
    section: Optional[str] = Field(None, min_length=1, max_length=100)

class StaticContent(StaticContentBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

# ========================
# RESPONSE MODELS
# ========================

class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    details: Optional[str] = None

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    pageSize: int
    totalPages: int

class SearchResult(BaseModel):
    type: str  # "program", "news", "event", "partnership"
    id: str
    title: str
    description: str
    url: str
    relevance: float = Field(default=1.0)
