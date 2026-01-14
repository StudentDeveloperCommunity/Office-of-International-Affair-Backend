from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
import os
import uuid
import hashlib
import logging
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, List

# Setup logging
logger = logging.getLogger(__name__)

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
# Read MONGO_URL from environment (or .env loaded earlier). Use getenv so we can give a helpful error
mongo_url = os.getenv('MONGO_URL')
if not mongo_url:
    raise ValueError(
        "MONGO_URL environment variable is not set.\n"
        "Set it in a local .env file or in your deployment environment.\n"
        "Example .env entry:\n"
        "MONGO_URL=\"mongodb+srv://USERNAME:PASSWORD@cluster0.example.mongodb.net/DB_NAME?retryWrites=true&w=majority\"\n"
    )

client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'medicapsoia')]

# ========================
# COLLECTIONS (v1 + v2.0)
# ========================
programs_collection = db.programs
contacts_collection = db.contacts
admins_collection = db.admins

# v2.0 New Collections
news_collection = db.news
partnerships_collection = db.partnerships
team_collection = db.team
events_collection = db.events
gallery_collection = db.gallery
faqs_collection = db.faqs
static_content_collection = db.static_content
stats_config_collection = db.stats_config

class DatabaseOperations:
    """Database operations for the OIA Website System"""

    @staticmethod
    async def get_stats_config() -> dict:
        """Get the stats configuration (admin-editable counters)."""
        doc = await stats_config_collection.find_one({'key': 'stats'})
        if not doc:
            return {'studentsExchanged': 150}
        return {
            'studentsExchanged': int(doc.get('studentsExchanged', 150))
        }

    @staticmethod
    async def update_stats_config(update_data: dict) -> dict:
        """Update stats configuration (upsert)."""
        update_data = {k: v for k, v in update_data.items() if v is not None}
        update_data['updatedAt'] = datetime.utcnow()
        await stats_config_collection.update_one(
            {'key': 'stats'},
            {'$set': update_data, '$setOnInsert': {'key': 'stats', 'createdAt': datetime.utcnow()}},
            upsert=True
        )
        return await DatabaseOperations.get_stats_config()

    # ========================
    # PROGRAM OPERATIONS (v1 - Retained)
    # ========================
    
    @staticmethod
    async def create_program(program_data: dict) -> dict:
        """Create a new program"""
        program_data['id'] = str(uuid.uuid4())
        program_data['createdAt'] = datetime.utcnow()
        program_data['updatedAt'] = datetime.utcnow()
        
        result = await programs_collection.insert_one(program_data)
        program_data['_id'] = str(result.inserted_id)
        return program_data

    @staticmethod
    async def get_programs(active_only: bool = True, page: int = 1, page_size: int = 50) -> dict:
        """Get all programs with pagination"""
        query = {'status': 'Active'} if active_only else {}
        
        total = await programs_collection.count_documents(query)
        skip = (page - 1) * page_size
        
        programs = await programs_collection.find(query).sort('createdAt', -1).skip(skip).limit(page_size).to_list(page_size)
        
        for program in programs:
            program['_id'] = str(program['_id'])
            if 'id' not in program:
                program['id'] = program['_id']
        
        return {
            'items': programs,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size
        }

    @staticmethod
    async def get_program_by_id(program_id: str) -> dict:
        """Get a specific program by ID"""
        program = await programs_collection.find_one({'id': program_id})
        if program:
            program['_id'] = str(program['_id'])
        return program

    @staticmethod
    async def update_program(program_id: str, update_data: dict) -> dict:
        """Update a program"""
        update_data['updatedAt'] = datetime.utcnow()
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = await programs_collection.update_one(
            {'id': program_id},
            {'$set': update_data}
        )
        
        if result.modified_count:
            return await DatabaseOperations.get_program_by_id(program_id)
        return None

    @staticmethod
    async def delete_program(program_id: str) -> bool:
        """Delete a program"""
        result = await programs_collection.delete_one({'id': program_id})
        return result.deleted_count > 0

    # ========================
    # NEWS OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def create_news(news_data: dict) -> dict:
        """Create a news article"""
        news_data['id'] = str(uuid.uuid4())
        news_data['createdAt'] = datetime.utcnow()
        news_data['updatedAt'] = datetime.utcnow()
        
        result = await news_collection.insert_one(news_data)
        news_data['_id'] = str(result.inserted_id)
        return news_data

    @staticmethod
    async def get_news(category: Optional[str] = None, page: int = 1, page_size: int = 10, featured_only: bool = False) -> dict:
        """Get news with pagination and filtering"""
        query = {}
        if category:
            query['category'] = category
        if featured_only:
            query['featured'] = True
            
        total = await news_collection.count_documents(query)
        skip = (page - 1) * page_size
        
        news_list = await news_collection.find(query).sort('date', -1).skip(skip).limit(page_size).to_list(page_size)
        
        for news in news_list:
            news['_id'] = str(news['_id'])
        
        return {
            'items': news_list,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size
        }

    @staticmethod
    async def get_news_by_id(news_id: str) -> dict:
        """Get a specific news article"""
        news = await news_collection.find_one({'id': news_id})
        if news:
            news['_id'] = str(news['_id'])
        return news

    @staticmethod
    async def update_news(news_id: str, update_data: dict) -> dict:
        """Update a news article"""
        update_data['updatedAt'] = datetime.utcnow()
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = await news_collection.update_one(
            {'id': news_id},
            {'$set': update_data}
        )
        
        if result.modified_count:
            return await DatabaseOperations.get_news_by_id(news_id)
        return None

    @staticmethod
    async def delete_news(news_id: str) -> bool:
        """Delete a news article"""
        result = await news_collection.delete_one({'id': news_id})
        return result.deleted_count > 0

    # ========================
    # PARTNERSHIP OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def create_partnership(partnership_data: dict) -> dict:
        """Create a partnership"""
        partnership_data['id'] = str(uuid.uuid4())
        partnership_data['createdAt'] = datetime.utcnow()
        partnership_data['updatedAt'] = datetime.utcnow()
        
        result = await partnerships_collection.insert_one(partnership_data)
        partnership_data['_id'] = str(result.inserted_id)
        return partnership_data

    @staticmethod
    async def get_partnerships(type: Optional[str] = None, country: Optional[str] = None, page: int = 1, page_size: int = 50) -> dict:
        """Get partnerships with filtering"""
        query = {}
        if type:
            query['type'] = type
        if country:
            query['country'] = country
            
        total = await partnerships_collection.count_documents(query)
        skip = (page - 1) * page_size
        
        partnerships = await partnerships_collection.find(query).sort('partnerName', 1).skip(skip).limit(page_size).to_list(page_size)
        
        for partnership in partnerships:
            partnership['_id'] = str(partnership['_id'])
        
        return {
            'items': partnerships,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size
        }

    @staticmethod
    async def get_partnership_by_id(partnership_id: str) -> dict:
        """Get a specific partnership"""
        partnership = await partnerships_collection.find_one({'id': partnership_id})
        if partnership:
            partnership['_id'] = str(partnership['_id'])
        return partnership

    @staticmethod
    async def update_partnership(partnership_id: str, update_data: dict) -> dict:
        """Update a partnership"""
        update_data['updatedAt'] = datetime.utcnow()
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = await partnerships_collection.update_one(
            {'id': partnership_id},
            {'$set': update_data}
        )
        
        if result.modified_count:
            return await DatabaseOperations.get_partnership_by_id(partnership_id)
        return None

    @staticmethod
    async def delete_partnership(partnership_id: str) -> bool:
        """Delete a partnership"""
        result = await partnerships_collection.delete_one({'id': partnership_id})
        return result.deleted_count > 0

    # ========================
    # TEAM OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def create_team_member(team_data: dict) -> dict:
        """Create a team member"""
        team_data['id'] = str(uuid.uuid4())
        team_data['createdAt'] = datetime.utcnow()
        team_data['updatedAt'] = datetime.utcnow()
        
        result = await team_collection.insert_one(team_data)
        team_data['_id'] = str(result.inserted_id)
        return team_data

    @staticmethod
    async def get_team_members() -> list:
        """Get all team members sorted by order"""
        members = await team_collection.find().sort('order', 1).to_list(100)
        
        for member in members:
            member['_id'] = str(member['_id'])
        
        return members

    @staticmethod
    async def get_team_member_by_id(member_id: str) -> dict:
        """Get a specific team member"""
        member = await team_collection.find_one({'id': member_id})
        if member:
            member['_id'] = str(member['_id'])
        return member

    @staticmethod
    async def update_team_member(member_id: str, update_data: dict) -> dict:
        """Update a team member"""
        update_data['updatedAt'] = datetime.utcnow()
        
        # Filter out None values and empty strings for optional fields only
        # Keep required fields even if empty (they should be validated at the form level)
        filtered_data = {}
        for k, v in update_data.items():
            if k in ['name', 'role', 'bio']:
                # Keep required fields even if empty
                if v is not None:
                    filtered_data[k] = v
            elif k == 'image':
                # Image field should allow empty strings for removal
                if v is not None:
                    filtered_data[k] = v
            else:
                # Filter out None values and empty strings for optional fields
                if v is not None and (isinstance(v, str) and v.strip() != '' or not isinstance(v, str)):
                    filtered_data[k] = v
        
        result = await team_collection.update_one(
            {'id': member_id},
            {'$set': filtered_data}
        )
        
        if result.modified_count:
            return await DatabaseOperations.get_team_member_by_id(member_id)
        return None

    @staticmethod
    async def delete_team_member(member_id: str) -> bool:
        """Delete a team member"""
        result = await team_collection.delete_one({'id': member_id})
        return result.deleted_count > 0

    # ========================
    # EVENT OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def create_event(event_data: dict) -> dict:
        """Create an event"""
        event_data['id'] = str(uuid.uuid4())
        event_data['createdAt'] = datetime.utcnow()
        event_data['updatedAt'] = datetime.utcnow()
        
        result = await events_collection.insert_one(event_data)
        event_data['_id'] = str(result.inserted_id)
        return event_data

    @staticmethod
    async def get_events(type: Optional[str] = None, page: int = 1, page_size: int = 20, upcoming_only: bool = False) -> dict:
        """Get events with filtering"""
        query = {}
        if type:
            query['type'] = type
        if upcoming_only:
            query['startDate'] = {'$gte': datetime.utcnow()}
            
        total = await events_collection.count_documents(query)
        skip = (page - 1) * page_size
        
        events = await events_collection.find(query).sort('startDate', -1).skip(skip).limit(page_size).to_list(page_size)
        
        for event in events:
            event['_id'] = str(event['_id'])
        
        return {
            'items': events,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size
        }

    @staticmethod
    async def get_event_by_id(event_id: str) -> dict:
        """Get a specific event"""
        event = await events_collection.find_one({'id': event_id})
        if event:
            event['_id'] = str(event['_id'])
        return event

    @staticmethod
    async def update_event(event_id: str, update_data: dict) -> dict:
        """Update an event"""
        update_data['updatedAt'] = datetime.utcnow()
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = await events_collection.update_one(
            {'id': event_id},
            {'$set': update_data}
        )
        
        if result.modified_count:
            return await DatabaseOperations.get_event_by_id(event_id)
        return None

    @staticmethod
    async def delete_event(event_id: str) -> bool:
        """Delete an event"""
        result = await events_collection.delete_one({'id': event_id})
        return result.deleted_count > 0

    # ========================
    # GALLERY OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def create_gallery_image(image_data: dict) -> dict:
        """Create a gallery image"""
        image_data['id'] = str(uuid.uuid4())
        image_data['uploadDate'] = datetime.utcnow()
        
        result = await gallery_collection.insert_one(image_data)
        image_data['_id'] = str(result.inserted_id)
        return image_data

    @staticmethod
    async def get_gallery_images(category: Optional[str] = None, page: int = 1, page_size: int = 30) -> dict:
        """Get gallery images with filtering"""
        query = {}
        if category:
            query['category'] = category
            
        total = await gallery_collection.count_documents(query)
        skip = (page - 1) * page_size
        
        images = await gallery_collection.find(query).sort('uploadDate', -1).skip(skip).limit(page_size).to_list(page_size)
        
        for image in images:
            image['_id'] = str(image['_id'])
        
        return {
            'items': images,
            'total': total,
            'page': page,
            'pageSize': page_size,
            'totalPages': (total + page_size - 1) // page_size
        }

    @staticmethod
    async def get_gallery_image_by_id(image_id: str) -> dict:
        """Get a specific gallery image"""
        image = await gallery_collection.find_one({'id': image_id})
        if image:
            image['_id'] = str(image['_id'])
        return image

    @staticmethod
    async def delete_gallery_image(image_id: str) -> bool:
        """Delete a gallery image"""
        result = await gallery_collection.delete_one({'id': image_id})
        return result.deleted_count > 0

    @staticmethod
    async def update_gallery_image(image_id: str, update_data: dict) -> dict:
        """Update a gallery image"""
        update_data = {k: v for k, v in update_data.items() if v is not None}
        result = await gallery_collection.update_one(
            {'id': image_id},
            {'$set': update_data}
        )
        if result.modified_count:
            return await DatabaseOperations.get_gallery_image_by_id(image_id)
        # If nothing modified, still return current image if it exists
        return await DatabaseOperations.get_gallery_image_by_id(image_id)

    # ========================
    # FAQ OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def create_faq(faq_data: dict) -> dict:
        """Create a FAQ"""
        faq_data['id'] = str(uuid.uuid4())
        faq_data['createdAt'] = datetime.utcnow()
        faq_data['updatedAt'] = datetime.utcnow()
        
        result = await faqs_collection.insert_one(faq_data)
        faq_data['_id'] = str(result.inserted_id)
        return faq_data

    @staticmethod
    async def get_faqs(category: Optional[str] = None) -> list:
        """Get FAQs by category"""
        query = {}
        if category:
            query['category'] = category
            
        faqs = await faqs_collection.find(query).sort('order', 1).to_list(500)
        
        for faq in faqs:
            faq['_id'] = str(faq['_id'])
        
        return faqs

    @staticmethod
    async def get_faq_by_id(faq_id: str) -> dict:
        """Get a specific FAQ"""
        faq = await faqs_collection.find_one({'id': faq_id})
        if faq:
            faq['_id'] = str(faq['_id'])
        return faq

    @staticmethod
    async def update_faq(faq_id: str, update_data: dict) -> dict:
        """Update a FAQ"""
        update_data['updatedAt'] = datetime.utcnow()
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = await faqs_collection.update_one(
            {'id': faq_id},
            {'$set': update_data}
        )
        
        if result.modified_count:
            return await DatabaseOperations.get_faq_by_id(faq_id)
        return None

    @staticmethod
    async def delete_faq(faq_id: str) -> bool:
        """Delete a FAQ"""
        result = await faqs_collection.delete_one({'id': faq_id})
        return result.deleted_count > 0

    # ========================
    # STATIC CONTENT OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def create_static_content(content_data: dict) -> dict:
        """Create static content"""
        content_data['id'] = str(uuid.uuid4())
        content_data['createdAt'] = datetime.utcnow()
        content_data['updatedAt'] = datetime.utcnow()
        
        result = await static_content_collection.insert_one(content_data)
        content_data['_id'] = str(result.inserted_id)
        return content_data

    @staticmethod
    async def get_static_content(section: Optional[str] = None) -> list:
        """Get static content by section"""
        query = {}
        if section:
            query['section'] = section
            
        content = await static_content_collection.find(query).to_list(100)
        
        for item in content:
            item['_id'] = str(item['_id'])
        
        return content

    @staticmethod
    async def get_static_content_by_key(key: str) -> dict:
        """Get static content by key"""
        content = await static_content_collection.find_one({'key': key})
        if content:
            content['_id'] = str(content['_id'])
        return content

    @staticmethod
    async def update_static_content(key: str, update_data: dict) -> dict:
        """Update static content"""
        update_data['updatedAt'] = datetime.utcnow()
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        result = await static_content_collection.update_one(
            {'key': key},
            {'$set': update_data}
        )
        
        if result.modified_count:
            return await DatabaseOperations.get_static_content_by_key(key)
        return None

    @staticmethod
    async def delete_static_content(key: str) -> bool:
        """Delete static content"""
        result = await static_content_collection.delete_one({'key': key})
        return result.deleted_count > 0

    # ========================
    # CONTACT OPERATIONS (v1 - Extended for v2.0)
    # ========================
    
    @staticmethod
    async def create_contact(contact_data: dict) -> dict:
        """Create a new contact submission"""
        contact_data['id'] = str(uuid.uuid4())
        contact_data['status'] = 'New'
        contact_data['createdAt'] = datetime.utcnow()
        
        result = await contacts_collection.insert_one(contact_data)
        contact_data['_id'] = str(result.inserted_id)
        return contact_data

    @staticmethod
    async def get_contacts(form_type: Optional[str] = None) -> list:
        """Get all contact submissions with optional type filter"""
        query = {}
        if form_type:
            query['formType'] = form_type
            
        contacts = await contacts_collection.find(query).sort('createdAt', -1).to_list(1000)
        
        for contact in contacts:
            contact['_id'] = str(contact['_id'])
            if 'id' not in contact:
                contact['id'] = contact['_id']
            
            # Normalize status values
            if 'status' in contact:
                if contact['status'] == 'read':
                    contact['status'] = 'Read'
                elif contact['status'] == 'new':
                    contact['status'] = 'New'
                elif contact['status'] == 'replied':
                    contact['status'] = 'Replied'
            else:
                contact['status'] = 'New'
        
        return contacts

    @staticmethod
    async def update_contact_status(contact_id: str, status: str) -> bool:
        """Update contact message status"""
        result = await contacts_collection.update_one(
            {'id': contact_id},
            {'$set': {'status': status}}
        )
        return result.modified_count > 0

    @staticmethod
    async def delete_contact(contact_id: str) -> bool:
        """Delete contact message"""
        result = await contacts_collection.delete_one({'id': contact_id})
        return result.deleted_count > 0

    # ========================
    # ADMIN OPERATIONS (v1 - Retained)
    # ========================
    
    @staticmethod
    async def create_admin(username: str, password: str) -> dict:
        """Create a new admin user"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        admin_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password': hashed_password,
            'role': 'admin',
            'createdAt': datetime.utcnow()
        }
        
        result = await admins_collection.insert_one(admin_data)
        admin_data['_id'] = str(result.inserted_id)
        return admin_data

    @staticmethod
    async def authenticate_admin(username: str, password: str) -> bool:
        """Authenticate admin credentials"""
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        admin = await admins_collection.find_one({
            'username': username,
            'password': hashed_password
        })
        
        return admin is not None

    # ========================
    # SEARCH OPERATIONS (v2.0 NEW)
    # ========================
    
    @staticmethod
    async def global_search(query: str, sections: Optional[List[str]] = None) -> dict:
        """Global search across multiple collections"""
        results = []
        
        # Search in programs
        if not sections or 'programs' in sections:
            programs = await programs_collection.find({
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}},
                    {'partnerUniversity': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(5).to_list(5)
            
            for prog in programs:
                results.append({
                    'type': 'program',
                    'id': prog.get('id', str(prog['_id'])),
                    'title': prog['title'],
                    'description': prog['description'][:200],
                    'url': f'/student-mobility/programs/{prog.get("id", str(prog["_id"]))}'
                })
        
        # Search in news
        if not sections or 'news' in sections:
            news = await news_collection.find({
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'content': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(5).to_list(5)
            
            for item in news:
                results.append({
                    'type': 'news',
                    'id': item['id'],
                    'title': item['title'],
                    'description': item['content'][:200],
                    'url': f'/news-media/{item["id"]}'
                })
        
        # Search in events
        if not sections or 'events' in sections:
            events = await events_collection.find({
                '$or': [
                    {'title': {'$regex': query, '$options': 'i'}},
                    {'description': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(5).to_list(5)
            
            for event in events:
                results.append({
                    'type': 'event',
                    'id': event['id'],
                    'title': event['title'],
                    'description': event['description'][:200],
                    'url': f'/visits-delegations-events/{event["id"]}'
                })
        
        # Search in partnerships
        if not sections or 'partnerships' in sections:
            partnerships = await partnerships_collection.find({
                '$or': [
                    {'partnerName': {'$regex': query, '$options': 'i'}},
                    {'details': {'$regex': query, '$options': 'i'}},
                    {'country': {'$regex': query, '$options': 'i'}}
                ]
            }).limit(5).to_list(5)
            
            for partner in partnerships:
                results.append({
                    'type': 'partnership',
                    'id': partner['id'],
                    'title': partner['partnerName'],
                    'description': partner['details'][:200],
                    'url': f'/global-partnerships/{partner["id"]}'
                })
        
        return {'results': results, 'total': len(results)}

    # ========================
    # STATS OPERATIONS (Extended for v2.0)
    # ========================
    
    @staticmethod
    async def get_stats() -> dict:
        """Get basic website statistics"""
        total_programs = await programs_collection.count_documents({'status': 'Active'})
        
        pipeline = [
            {'$match': {'status': 'Active'}},
            {'$group': {'_id': '$partnerUniversity'}}
        ]
        partner_unis = await programs_collection.aggregate(pipeline).to_list(1000)
        
        config = await DatabaseOperations.get_stats_config()

        return {
            'totalPrograms': total_programs,
            'partnerUniversities': len(partner_unis),
            'studentsExchanged': config.get('studentsExchanged', 150),
            'countries': 12
        }

    @staticmethod
    async def get_extended_stats() -> dict:
        """Get extended statistics for v2.0"""
        stats = await DatabaseOperations.get_stats()
        
        total_events = await events_collection.count_documents({})
        active_partnerships = await partnerships_collection.count_documents({'status': 'Active'})
        news_articles = await news_collection.count_documents({})
        team_members = await team_collection.count_documents({})
        
        stats.update({
            'totalEvents': total_events,
            'activePartnerships': active_partnerships,
            'internationalStudents': 250,
            'newsArticles': news_articles,
            'teamMembers': team_members
        })
        
        return stats


# ========================
# DATABASE INITIALIZATION with SEEDING (v2.0)
# ========================

async def initialize_database():
    """Initialize database with sample data for v1 + v2.0"""
    
    # Check if admin exists, if not create one
    existing_admin = await admins_collection.find_one({'username': 'medicaps_admin_2025'})
    if not existing_admin:
        await DatabaseOperations.create_admin('medicaps_admin_2025', 'MediCaps$Secure#2025!Exchange@Admin')
        print("✅ Default admin created")

    # Seed Programs (v1 - clear and reseed)
    existing_programs = await programs_collection.count_documents({})
    if existing_programs == 0:
        sample_programs = [
            {
                'title': 'Engineering Innovation - Stanford University',
                'description': 'Advanced engineering program focusing on Silicon Valley innovation, startup methodologies, and cutting-edge technology development with hands-on industry exposure.',
                'partnerUniversity': 'Stanford University, USA',
                'duration': '1 Semester (5 months)',
                'eligibility': '3rd/4th year Engineering students with CGPA ≥ 8.0',
                'deadline': 'January 20, 2025',
                'applicationLink': 'https://forms.google.com/stanford-engineering',
                'status': 'Active'
            },
            {
                'title': 'International Business - London School of Economics',
                'description': 'Global business strategy program offering deep insights into international markets, finance, and economic policy.',
                'partnerUniversity': 'London School of Economics, UK',
                'duration': '6 months',
                'eligibility': 'MBA/BBA students with minimum 80% marks',
                'deadline': 'March 10, 2025',
                'applicationLink': 'https://forms.google.com/lse-business',
                'status': 'Active'
            },
            {
                'title': 'Computer Science & AI - ETH Zurich',
                'description': 'World-class computer science program specializing in artificial intelligence, machine learning, and quantum computing.',
                'partnerUniversity': 'ETH Zurich, Switzerland',
                'duration': '1 Academic Year',
                'eligibility': 'CS/IT students with CGPA ≥ 8.5 and research experience',
                'deadline': 'December 30, 2024',
                'applicationLink': 'https://forms.google.com/eth-cs',
                'status': 'Active'
            }
        ]
        
        for program in sample_programs:
            await DatabaseOperations.create_program(program)
        
        print(f"✅ Seeded {len(sample_programs)} programs")

    # Seed News (v2.0)
    existing_news = await news_collection.count_documents({})
    if existing_news == 0:
        sample_news = [
            {
                'title': 'New MoU Signed with Harvard University',
                'content': 'Medi-Caps University is proud to announce a new Memorandum of Understanding with Harvard University for collaborative research and student exchange programs. This partnership will open new avenues for our students to experience world-class education.',
                'category': 'MoU',
                'date': datetime(2025, 12, 1),
                'author': 'OIA Team',
                'tags': ['partnership', 'harvard', 'mou'],
                'featured': True
            },
            {
                'title': 'Students Win International Innovation Award',
                'content': 'Three Medi-Caps students have won the prestigious Global Innovation Challenge in Berlin, competing against 200+ teams from 50 countries.',
                'category': 'Achievement',
                'date': datetime(2025, 11, 15),
                'author': 'OIA Team',
                'tags': ['achievement', 'students', 'innovation'],
                'featured': True
            },
            {
                'title': 'International Research Collaboration Summit 2025',
                'content': 'Join us for the annual research collaboration summit featuring keynote speakers from MIT, Oxford, and Stanford. Registration now open.',
                'category': 'Announcement',
                'date': datetime(2025, 10, 20),
                'author': 'Dr. Sharma',
                'tags': ['event', 'research', 'collaboration'],
                'featured': False
            },
            {
                'title': 'New Scholarship Program for International Students',
                'content': 'Announcing a new scholarship program covering 50% tuition for exceptional international students. Applications open from January 2025.',
                'category': 'Announcement',
                'date': datetime(2025, 9, 5),
                'author': 'OIA Team',
                'tags': ['scholarship', 'admissions'],
                'featured': True
            },
            {
                'title': 'Faculty Exchange Program with Tokyo University',
                'content': 'Dr. Patel successfully completed a 3-month research fellowship at Tokyo University, strengthening our academic ties with Japan.',
                'category': 'Achievement',
                'date': datetime(2025, 8, 10),
                'author': 'OIA Team',
                'tags': ['faculty', 'japan', 'exchange'],
                'featured': False
            }
        ]
        
        for news in sample_news:
            await DatabaseOperations.create_news(news)
        
        print(f"✅ Seeded {len(sample_news)} news articles")

    # Seed Partnerships (v2.0)
    existing_partnerships = await partnerships_collection.count_documents({})
    if existing_partnerships == 0:
        sample_partnerships = [
            {
                'partnerName': 'Massachusetts Institute of Technology (MIT)',
                'type': 'Research',
                'country': 'United States',
                'details': 'Collaborative research in AI, robotics, and sustainable technology. Joint PhD programs available.',
                'status': 'Active',
                'signedDate': datetime(2023, 5, 15),
                'website': 'https://www.mit.edu',
                'benefits': ['Research collaboration', 'Student exchange', 'Faculty visits']
            },
            {
                'partnerName': 'University of Oxford',
                'type': 'Dual Degree',
                'country': 'United Kingdom',
                'details': 'Dual degree programs in Medicine and Life Sciences with full credit transfer.',
                'status': 'Active',
                'signedDate': datetime(2022, 9, 20),
                'website': 'https://www.ox.ac.uk',
                'benefits': ['Dual degrees', 'Research opportunities', 'Scholarships']
            },
            {
                'partnerName': 'National University of Singapore',
                'type': 'Student Exchange',
                'country': 'Singapore',
                'details': 'Semester exchange programs for engineering and business students.',
                'status': 'Active',
                'signedDate': datetime(2024, 2, 10),
                'website': 'https://www.nus.edu.sg',
                'benefits': ['Semester exchange', 'Cultural immersion', 'Industry exposure']
            },
            {
                'partnerName': 'Sorbonne University',
                'type': 'Strategic',
                'country': 'France',
                'details': 'Strategic partnership covering multiple faculties including arts, science, and engineering.',
                'status': 'Active',
                'signedDate': datetime(2023, 11, 5),
                'website': 'https://www.sorbonne-universite.fr',
                'benefits': ['Multiple programs', 'Language courses', 'Cultural exchange']
            },
            {
                'partnerName': 'University of Melbourne',
                'type': 'Research',
                'country': 'Australia',
                'details': 'Joint research initiatives in environmental science and climate change.',
                'status': 'Active',
                'signedDate': datetime(2024, 1, 18),
                'website': 'https://www.unimelb.edu.au',
                'benefits': ['Research grants', 'Field studies', 'Publications']
            }
        ]
        
        for partnership in sample_partnerships:
            await DatabaseOperations.create_partnership(partnership)
        
        print(f"✅ Seeded {len(sample_partnerships)} partnerships")

    # Seed Team Members (v2.0)
    existing_team = await team_collection.count_documents({})
    if existing_team == 0:
        sample_team = [
            {
                'name': 'Dr. Rajesh Kumar',
                'role': 'Director, Office of International Affairs',
                'bio': 'Dr. Kumar has over 20 years of experience in international education and has established partnerships with 50+ universities worldwide.',
                'email': 'rajesh.kumar@medicaps.ac.in',
                'phone': '+91-731-1234567',
                'office': 'Admin Block, Room 301',
                'responsibilities': ['Strategic partnerships', 'Policy development', 'International collaborations'],
                'order': 1
            },
            {
                'name': 'Prof. Priya Sharma',
                'role': 'Associate Director, Student Mobility',
                'bio': 'Prof. Sharma specializes in student exchange programs and has coordinated mobility for over 500 students.',
                'email': 'priya.sharma@medicaps.ac.in',
                'phone': '+91-731-1234568',
                'office': 'Admin Block, Room 302',
                'responsibilities': ['Student exchanges', 'Program coordination', 'Student counseling'],
                'order': 2
            },
            {
                'name': 'Mr. Anil Verma',
                'role': 'Manager, International Admissions',
                'bio': 'Mr. Verma handles all international admissions and visa support services.',
                'email': 'anil.verma@medicaps.ac.in',
                'phone': '+91-731-1234569',
                'office': 'Admin Block, Room 305',
                'responsibilities': ['Admissions processing', 'Visa assistance', 'Documentation'],
                'order': 3
            },
            {
                'name': 'Ms. Sneha Patel',
                'role': 'Coordinator, Faculty Mobility',
                'bio': 'Ms. Patel coordinates faculty exchange programs and research collaborations.',
                'email': 'sneha.patel@medicaps.ac.in',
                'phone': '+91-731-1234570',
                'office': 'Admin Block, Room 306',
                'responsibilities': ['Faculty exchanges', 'Research collaboration', 'Conference coordination'],
                'order': 4
            }
        ]
        
        for member in sample_team:
            await DatabaseOperations.create_team_member(member)
        
        print(f"✅ Seeded {len(sample_team)} team members")

    # Seed Events (v2.0)
    existing_events = await events_collection.count_documents({})
    if existing_events == 0:
        sample_events = [
            {
                'title': 'International Education Fair 2025',
                'type': 'Conference',
                'description': 'Annual education fair featuring representatives from 30+ international universities.',
                'startDate': datetime(2025, 3, 15, 10, 0),
                'endDate': datetime(2025, 3, 15, 17, 0),
                'venue': 'Medi-Caps Main Auditorium',
                'organizer': 'Office of International Affairs',
                'participants': ['Harvard', 'MIT', 'Oxford', 'Cambridge'],
                'featured': True
            },
            {
                'title': 'Global Research Collaboration Webinar',
                'type': 'Webinar',
                'description': 'Webinar on establishing international research partnerships and funding opportunities.',
                'startDate': datetime(2025, 2, 20, 15, 0),
                'endDate': datetime(2025, 2, 20, 17, 0),
                'venue': 'Online (Zoom)',
                'organizer': 'Dr. Rajesh Kumar',
                'featured': True,
                'registrationLink': 'https://zoom.us/webinar/register'
            },
            {
                'title': 'Cultural Exchange Program with Japan',
                'type': 'Visit',
                'description': 'Student delegation visit to Tokyo University for cultural and academic exchange.',
                'startDate': datetime(2024, 12, 5, 9, 0),
                'endDate': datetime(2024, 12, 12, 18, 0),
                'venue': 'Tokyo, Japan',
                'organizer': 'Prof. Priya Sharma',
                'participants': ['20 students', '2 faculty members'],
                'featured': False
            },
            {
                'title': 'International Alumni Meet 2025',
                'type': 'Conference',
                'description': 'Annual gathering of international alumni to network and share experiences.',
                'startDate': datetime(2025, 4, 10, 11, 0),
                'endDate': datetime(2025, 4, 10, 16, 0),
                'venue': 'Medi-Caps Convention Center',
                'organizer': 'Alumni Relations',
                'featured': True
            },
            {
                'title': 'Study Abroad Orientation Session',
                'type': 'Seminar',
                'description': 'Comprehensive orientation for students planning to study abroad in Fall 2025.',
                'startDate': datetime(2025, 1, 25, 14, 0),
                'endDate': datetime(2025, 1, 25, 16, 0),
                'venue': 'Seminar Hall A',
                'organizer': 'Student Mobility Office',
                'featured': False
            }
        ]
        
        for event in sample_events:
            await DatabaseOperations.create_event(event)
        
        print(f"✅ Seeded {len(sample_events)} events")

    # Seed FAQs (v2.0)
    existing_faqs = await faqs_collection.count_documents({})
    if existing_faqs == 0:
        sample_faqs = [
            {
                'question': 'How do I apply for student exchange programs?',
                'answer': 'To apply for student exchange programs, visit the Student Mobility section, select your desired program, and fill out the online application form. Ensure you meet the eligibility criteria and submit all required documents.',
                'category': 'Mobility',
                'order': 1,
                'featured': True
            },
            {
                'question': 'What are the admission requirements for international students?',
                'answer': 'International students must have completed equivalent of 12 years of schooling, meet English proficiency requirements (IELTS 6.5 or equivalent), and submit transcripts, passport copy, and other documents as specified in the admissions portal.',
                'category': 'Admissions',
                'order': 2,
                'featured': True
            },
            {
                'question': 'Do I need a visa to study at Medi-Caps University?',
                'answer': 'Yes, international students require a Student Visa (S-Visa) to study in India. Our International Admissions office provides comprehensive visa support and FRRO registration assistance.',
                'category': 'Visas',
                'order': 3,
                'featured': True
            },
            {
                'question': 'What scholarship opportunities are available?',
                'answer': 'We offer merit-based scholarships covering 25-50% of tuition fees for exceptional students. Additional country-specific scholarships and government-funded programs are also available.',
                'category': 'Admissions',
                'order': 4,
                'featured': False
            },
            {
                'question': 'How can my university partner with Medi-Caps?',
                'answer': 'Universities interested in partnership can submit a proposal through the Global Partnerships section. Our team will review and contact you within 2 weeks to discuss collaboration opportunities.',
                'category': 'Partnerships',
                'order': 5,
                'featured': False
            },
            {
                'question': 'Is accommodation provided for international students?',
                'answer': 'Yes, we provide on-campus hostel facilities for international students with modern amenities, dining halls, and recreational facilities. Off-campus accommodation assistance is also available.',
                'category': 'General',
                'order': 6,
                'featured': False
            }
        ]
        
        for faq in sample_faqs:
            await DatabaseOperations.create_faq(faq)
        
        print(f"✅ Seeded {len(sample_faqs)} FAQs")

    # Seed Static Content (v2.0)
    existing_static = await static_content_collection.count_documents({})
    if existing_static == 0:
        sample_static = [
            {
                'key': 'vision_mission',
                'title': 'Vision & Mission',
                'content': '''# Our Vision
To establish Medi-Caps University as a globally recognized institution fostering international collaboration, cultural diversity, and academic excellence.

# Our Mission
- Promote student and faculty mobility through strategic partnerships
- Facilitate research collaboration with leading international institutions
- Provide comprehensive support to international students and scholars
- Develop innovative programs that prepare students for global careers
- Build sustainable relationships with universities, industries, and governments worldwide''',
                'section': 'about'
            },
            {
                'key': 'policies',
                'title': 'International Policies & Guidelines',
                'content': '''# Credit Transfer Policy
All partner universities follow ECTS (European Credit Transfer System) with 1:1 credit mapping. Students must complete minimum 12 credits per semester abroad.

# Visa Policy
Student visa applications must be submitted 6 weeks before program start. We provide complete FRRO registration support.

# Code of Conduct
All participants must adhere to host institution policies and represent Medi-Caps University professionally.

# Insurance Requirements
Mandatory health and travel insurance for all outbound students. Coverage details available in student handbook.''',
                'section': 'about'
            },
            {
                'key': 'why_medicaps',
                'title': 'Why Choose Medi-Caps University?',
                'content': '''# Academic Excellence
- NAAC A+ accredited institution
- 50+ international partnerships
- World-class faculty and research facilities

# Global Exposure
- Student exchange programs in 15+ countries
- International internship opportunities
- Multicultural campus environment

# Career Support
- Dedicated placement cell with global recruiters
- Alumni network across 25 countries
- Industry-aligned curriculum

# Affordable Education
- Competitive tuition fees
- Multiple scholarship opportunities
- Modern campus facilities''',
                'section': 'admissions'
            }
        ]
        
        for content in sample_static:
            await DatabaseOperations.create_static_content(content)
        
        print(f"✅ Seeded {len(sample_static)} static content items")

    print("🚀 Database initialization complete - v2.0 OIA Website")
