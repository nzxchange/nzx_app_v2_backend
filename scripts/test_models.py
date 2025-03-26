import os
import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from app.models.organization import Organization, OrganizationCreate
from datetime import datetime
import uuid

def test_organization_models():
    # Test creating an organization
    org_data = {
        "name": "Test Corp",
        "domain": "test.com",
        "registration_number": "TEST123",
        "address": "123 Test St"
    }
    
    try:
        # Test OrganizationCreate
        org_create = OrganizationCreate(**org_data)
        print("✅ OrganizationCreate model works")
        
        # Test Organization
        org_full_data = {
            **org_data,
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        org = Organization(**org_full_data)
        print("✅ Organization model works")
        print(f"Created organization: {org.model_dump_json(indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Error testing models: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing organization models...")
    success = test_organization_models()
    sys.exit(0 if success else 1) 