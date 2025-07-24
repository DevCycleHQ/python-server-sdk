#!/usr/bin/env python3
"""
Simple test for config metadata functionality without external dependencies
"""

import sys
import os

# Add the SDK to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'devcycle_python_sdk'))

# Mock the missing dependencies
class MockUser:
    def __init__(self, user_id):
        self.user_id = user_id

# Test the config metadata classes
def test_project_metadata():
    """Test ProjectMetadata functionality"""
    from models.config_metadata import ProjectMetadata
    
    # Test creation
    project = ProjectMetadata(id="test-id", key="test-key")
    assert project.id == "test-id"
    assert project.key == "test-key"
    
    # Test from_json
    data = {"_id": "json-id", "key": "json-key"}
    project = ProjectMetadata.from_json(data)
    assert project.id == "json-id"
    assert project.key == "json-key"
    
    print("✅ ProjectMetadata tests passed")

def test_environment_metadata():
    """Test EnvironmentMetadata functionality"""
    from models.config_metadata import EnvironmentMetadata
    
    # Test creation
    env = EnvironmentMetadata(id="env-id", key="env-key")
    assert env.id == "env-id"
    assert env.key == "env-key"
    
    # Test from_json
    data = {"_id": "json-env-id", "key": "json-env-key"}
    env = EnvironmentMetadata.from_json(data)
    assert env.id == "json-env-id"
    assert env.key == "json-env-key"
    
    print("✅ EnvironmentMetadata tests passed")

def test_config_metadata():
    """Test ConfigMetadata functionality"""
    from models.config_metadata import ConfigMetadata, ProjectMetadata, EnvironmentMetadata
    
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
    
    # Test from_config_response
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
    
    # Test string representation
    str_repr = str(metadata)
    assert "etag=etag-123" in str_repr
    assert "last_modified=2023-01-01T00:00:00Z" in str_repr
    
    print("✅ ConfigMetadata tests passed")

def test_hook_context_metadata():
    """Test HookContext with metadata"""
    from models.config_metadata import ConfigMetadata, ProjectMetadata, EnvironmentMetadata
    from models.eval_hook_context import HookContext
    
    # Mock user
    user = MockUser("test-user")
    
    # Create metadata
    metadata = ConfigMetadata(
        config_etag="etag-123",
        config_last_modified="2023-01-01T00:00:00Z",
        project=ProjectMetadata(id="proj-id", key="proj-key"),
        environment=EnvironmentMetadata(id="env-id", key="env-key")
    )
    
    # Test HookContext with metadata
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
    from util.json_utils import JSONUtils
    import json
    
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

def main():
    """Run all tests"""
    print("🧪 Running config metadata tests...")
    
    try:
        test_project_metadata()
        test_environment_metadata()
        test_config_metadata()
        test_hook_context_metadata()
        test_json_utils()
        
        print("\n🎉 All tests passed! Config metadata implementation is working correctly.")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())