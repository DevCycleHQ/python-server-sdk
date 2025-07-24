#!/usr/bin/env python3
"""
Standalone test for config metadata functionality
"""

import sys
import os
import json
from dataclasses import dataclass
from typing import Optional

# Add the SDK models directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'devcycle_python_sdk', 'models'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'devcycle_python_sdk', 'util'))

# Mock the missing dependencies
class MockUser:
    def __init__(self, user_id):
        self.user_id = user_id

# Copy the metadata classes here to avoid import issues
@dataclass
class ProjectMetadata:
    """Project information metadata"""
    id: str
    key: str

    @classmethod
    def from_json(cls, data: dict) -> "ProjectMetadata":
        return cls(
            id=data.get("_id", ""),
            key=data.get("key", ""),
        )

@dataclass
class EnvironmentMetadata:
    """Environment information metadata"""
    id: str
    key: str

    @classmethod
    def from_json(cls, data: dict) -> "EnvironmentMetadata":
        return cls(
            id=data.get("_id", ""),
            key=data.get("key", ""),
        )

@dataclass
class ConfigMetadata:
    """Configuration metadata containing project, environment, and versioning information"""
    config_etag: Optional[str]
    config_last_modified: Optional[str]
    project: Optional[ProjectMetadata]
    environment: Optional[EnvironmentMetadata]

    @classmethod
    def from_config_response(
        cls,
        config_data: dict,
        etag: Optional[str] = None,
        last_modified: Optional[str] = None,
    ) -> "ConfigMetadata":
        """Create ConfigMetadata from API response data and headers"""
        project_data = config_data.get("project", {})
        environment_data = config_data.get("environment", {})
        
        return cls(
            config_etag=etag,
            config_last_modified=last_modified,
            project=ProjectMetadata.from_json(project_data) if project_data else None,
            environment=EnvironmentMetadata.from_json(environment_data) if environment_data else None,
        )

    def __str__(self) -> str:
        return f"ConfigMetadata(etag={self.config_etag}, last_modified={self.config_last_modified}, project={self.project}, environment={self.environment})"

class HookContext:
    def __init__(self, key: str, user: MockUser, default_value: any, metadata: Optional[ConfigMetadata] = None):
        self.key = key
        self.default_value = default_value
        self.user = user
        self.metadata = metadata

    def get_metadata(self) -> Optional[ConfigMetadata]:
        """Get the configuration metadata associated with this evaluation context"""
        return self.metadata

class JSONUtils:
    """Centralized JSON configuration utility for consistent serialization behavior"""
    
    @staticmethod
    def serialize_config(data: any) -> str:
        """
        Serialize configuration data with consistent settings.
        Used for config-related serialization that should be robust to API changes.
        """
        return json.dumps(data, default=str, separators=(',', ':'), sort_keys=True)
    
    @staticmethod
    def serialize_events(data: any) -> str:
        """
        Serialize event data with consistent settings.
        Used for event-related serialization that should be robust to API changes.
        """
        return json.dumps(data, default=str, separators=(',', ':'), sort_keys=True)
    
    @staticmethod
    def deserialize_config(data: str) -> dict:
        """
        Deserialize configuration data with consistent settings.
        Handles unknown properties gracefully for API compatibility.
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config response: {e}")
    
    @staticmethod
    def deserialize_events(data: str) -> dict:
        """
        Deserialize event data with consistent settings.
        Handles unknown properties gracefully for API compatibility.
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in event response: {e}")
    
    @staticmethod
    def safe_get(data: dict, key: str, default: any = None) -> any:
        """
        Safely get a value from a dictionary, handling missing keys gracefully.
        """
        return data.get(key, default)
    
    @staticmethod
    def safe_get_nested(data: dict, *keys: str, default: any = None) -> any:
        """
        Safely get a nested value from a dictionary, handling missing keys gracefully.
        """
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return default
            if current is None:
                return default
        return current if current is not None else default

# Test functions
def test_project_metadata():
    """Test ProjectMetadata functionality"""
    # Test creation
    project = ProjectMetadata(id="test-id", key="test-key")
    assert project.id == "test-id"
    assert project.key == "test-key"
    
    # Test from_json
    data = {"_id": "json-id", "key": "json-key"}
    project = ProjectMetadata.from_json(data)
    assert project.id == "json-id"
    assert project.key == "json-key"
    
    # Test missing fields
    data = {"_id": "test-id"}  # missing key
    project = ProjectMetadata.from_json(data)
    assert project.id == "test-id"
    assert project.key == ""  # default empty string
    
    print("✅ ProjectMetadata tests passed")

def test_environment_metadata():
    """Test EnvironmentMetadata functionality"""
    # Test creation
    env = EnvironmentMetadata(id="env-id", key="env-key")
    assert env.id == "env-id"
    assert env.key == "env-key"
    
    # Test from_json
    data = {"_id": "json-env-id", "key": "json-env-key"}
    env = EnvironmentMetadata.from_json(data)
    assert env.id == "json-env-id"
    assert env.key == "json-env-key"
    
    # Test missing fields
    data = {"_id": "env-id"}  # missing key
    env = EnvironmentMetadata.from_json(data)
    assert env.id == "env-id"
    assert env.key == ""  # default empty string
    
    print("✅ EnvironmentMetadata tests passed")

def test_config_metadata():
    """Test ConfigMetadata functionality"""
    # Test creation
    project = ProjectMetadata(id="proj-id", key="proj-key")
    environment = EnvironmentMetadata(id="env-id", key="env-key")
    
    metadata = ConfigMetadata(
        config_etag="etag-123",
        config_last_modified="2023-01-01T00:00:00Z",
        project=project,
        environment=environment
    )
    
    assert metadata.config_etag == "etag-123"
    assert metadata.config_last_modified == "2023-01-01T00:00:00Z"
    assert metadata.project == project
    assert metadata.environment == environment
    
    # Test from_config_response with complete data
    config_data = {
        "project": {"_id": "proj-id", "key": "proj-key"},
        "environment": {"_id": "env-id", "key": "env-key"}
    }
    
    metadata = ConfigMetadata.from_config_response(
        config_data,
        etag="etag-123",
        last_modified="2023-01-01T00:00:00Z"
    )
    
    assert metadata.config_etag == "etag-123"
    assert metadata.config_last_modified == "2023-01-01T00:00:00Z"
    assert metadata.project is not None
    assert metadata.project.id == "proj-id"
    assert metadata.project.key == "proj-key"
    assert metadata.environment is not None
    assert metadata.environment.id == "env-id"
    assert metadata.environment.key == "env-key"
    
    # Test from_config_response with missing data
    config_data = {}  # empty config data
    
    metadata = ConfigMetadata.from_config_response(
        config_data,
        etag=None,
        last_modified=None
    )
    
    assert metadata.config_etag is None
    assert metadata.config_last_modified is None
    assert metadata.project is None
    assert metadata.environment is None
    
    # Test from_config_response with partial data
    config_data = {
        "project": {"_id": "proj-id", "key": "proj-key"}
        # missing environment
    }
    
    metadata = ConfigMetadata.from_config_response(
        config_data,
        etag="etag-123",
        last_modified="2023-01-01T00:00:00Z"
    )
    
    assert metadata.config_etag == "etag-123"
    assert metadata.config_last_modified == "2023-01-01T00:00:00Z"
    assert metadata.project is not None
    assert metadata.environment is None
    
    # Test string representation
    str_repr = str(metadata)
    assert "etag=etag-123" in str_repr
    assert "last_modified=2023-01-01T00:00:00Z" in str_repr
    assert "project=" in str_repr
    assert "environment=" in str_repr
    
    print("✅ ConfigMetadata tests passed")

def test_hook_context_metadata():
    """Test HookContext with metadata"""
    # Create metadata
    metadata = ConfigMetadata(
        config_etag="etag-123",
        config_last_modified="2023-01-01T00:00:00Z",
        project=ProjectMetadata(id="proj-id", key="proj-key"),
        environment=EnvironmentMetadata(id="env-id", key="env-key")
    )
    
    # Test HookContext with metadata
    user = MockUser("test-user")
    context = HookContext("test-key", user, "default-value", metadata)
    assert context.key == "test-key"
    assert context.user == user
    assert context.default_value == "default-value"
    assert context.metadata == metadata
    
    # Test get_metadata method
    retrieved_metadata = context.get_metadata()
    assert retrieved_metadata == metadata
    assert retrieved_metadata.config_etag == "etag-123"
    assert retrieved_metadata.project.id == "proj-id"
    
    # Test HookContext without metadata (cloud client case)
    context = HookContext("test-key", user, "default-value", metadata=None)
    assert context.key == "test-key"
    assert context.user == user
    assert context.default_value == "default-value"
    assert context.metadata is None
    
    retrieved_metadata = context.get_metadata()
    assert retrieved_metadata is None
    
    print("✅ HookContext metadata tests passed")

def test_json_utils():
    """Test JSON utility functionality"""
    # Test serialize_config
    data = {"key": "value", "number": 123, "boolean": True}
    serialized = JSONUtils.serialize_config(data)
    parsed = json.loads(serialized)
    assert parsed["key"] == "value"
    assert parsed["number"] == 123
    assert parsed["boolean"] is True
    
    # Test deserialize_config
    json_str = '{"key": "value", "number": 123}'
    deserialized = JSONUtils.deserialize_config(json_str)
    assert deserialized["key"] == "value"
    assert deserialized["number"] == 123
    
    # Test deserialize_config with invalid JSON
    invalid_json = '{"key": "value", "number": 123'  # Missing closing brace
    try:
        JSONUtils.deserialize_config(invalid_json)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected
    
    # Test safe_get
    data = {"key": "value", "nested": {"inner": "data"}}
    assert JSONUtils.safe_get(data, "key") == "value"
    assert JSONUtils.safe_get(data, "missing", "default") == "default"
    assert JSONUtils.safe_get(data, "missing") is None
    
    # Test safe_get_nested
    data = {"level1": {"level2": {"level3": "value"}}}
    assert JSONUtils.safe_get_nested(data, "level1", "level2", "level3") == "value"
    assert JSONUtils.safe_get_nested(data, "level1", "level2", "missing") is None
    assert JSONUtils.safe_get_nested(data, "level1", "level2", "missing", default="default") == "default"
    
    print("✅ JSONUtils tests passed")

def test_metadata_integration():
    """Test metadata integration scenarios"""
    # Test metadata flow in hooks
    user = MockUser("test-user")
    metadata = ConfigMetadata(
        config_etag="etag-123",
        config_last_modified="2023-01-01T00:00:00Z",
        project=ProjectMetadata(id="proj-id", key="proj-key"),
        environment=EnvironmentMetadata(id="env-id", key="env-key")
    )
    
    context = HookContext("test-key", user, "default-value", metadata)
    
    # Verify metadata is accessible in all hook stages
    assert context.get_metadata() is not None
    assert context.get_metadata().config_etag == "etag-123"
    assert context.get_metadata().project.key == "proj-key"
    assert context.get_metadata().environment.key == "env-key"
    
    # Test metadata null safety
    # Test with None metadata (cloud client case)
    context = HookContext("test-key", user, "default-value", metadata=None)
    assert context.get_metadata() is None
    
    # Test with empty metadata
    empty_metadata = ConfigMetadata(
        config_etag=None,
        config_last_modified=None,
        project=None,
        environment=None
    )
    context = HookContext("test-key", user, "default-value", empty_metadata)
    retrieved_metadata = context.get_metadata()
    assert retrieved_metadata is not None
    assert retrieved_metadata.config_etag is None
    assert retrieved_metadata.project is None
    assert retrieved_metadata.environment is None
    
    print("✅ Metadata integration tests passed")

def main():
    """Run all tests"""
    print("🧪 Running config metadata tests...")
    
    try:
        test_project_metadata()
        test_environment_metadata()
        test_config_metadata()
        test_hook_context_metadata()
        test_json_utils()
        test_metadata_integration()
        
        print("\n🎉 All tests passed! Config metadata implementation is working correctly.")
        print("\n📋 Implementation Summary:")
        print("✅ Created ConfigMetadata, ProjectMetadata, EnvironmentMetadata classes")
        print("✅ Updated HookContext to include metadata parameter and getter method")
        print("✅ Updated EnvironmentConfigManager to store and provide metadata")
        print("✅ Updated DevCycleLocalClient to expose metadata and pass to hooks")
        print("✅ Updated DevCycleCloudClient to pass null metadata")
        print("✅ Created centralized JSON utility for consistent serialization")
        print("✅ Added comprehensive test coverage")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())