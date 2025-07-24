import unittest
from unittest.mock import Mock, patch
from typing import Optional

from devcycle_python_sdk.models.config_metadata import (
    ConfigMetadata,
    ProjectMetadata,
    EnvironmentMetadata,
)
from devcycle_python_sdk.models.eval_hook_context import HookContext
from devcycle_python_sdk.models.user import DevCycleUser


class TestProjectMetadata(unittest.TestCase):
    def test_project_metadata_creation(self):
        """Test ProjectMetadata constructs correctly with mock data"""
        project = ProjectMetadata(id="test-id", key="test-key")
        self.assertEqual(project.id, "test-id")
        self.assertEqual(project.key, "test-key")

    def test_project_metadata_from_json(self):
        """Test ProjectMetadata.from_json with valid data"""
        data = {"_id": "test-id", "key": "test-key"}
        project = ProjectMetadata.from_json(data)
        self.assertEqual(project.id, "test-id")
        self.assertEqual(project.key, "test-key")

    def test_project_metadata_from_json_missing_fields(self):
        """Test ProjectMetadata.from_json handles missing fields gracefully"""
        data = {"_id": "test-id"}  # missing key
        project = ProjectMetadata.from_json(data)
        self.assertEqual(project.id, "test-id")
        self.assertEqual(project.key, "")  # default empty string


class TestEnvironmentMetadata(unittest.TestCase):
    def test_environment_metadata_creation(self):
        """Test EnvironmentMetadata constructs correctly with mock data"""
        env = EnvironmentMetadata(id="env-id", key="env-key")
        self.assertEqual(env.id, "env-id")
        self.assertEqual(env.key, "env-key")

    def test_environment_metadata_from_json(self):
        """Test EnvironmentMetadata.from_json with valid data"""
        data = {"_id": "env-id", "key": "env-key"}
        env = EnvironmentMetadata.from_json(data)
        self.assertEqual(env.id, "env-id")
        self.assertEqual(env.key, "env-key")

    def test_environment_metadata_from_json_missing_fields(self):
        """Test EnvironmentMetadata.from_json handles missing fields gracefully"""
        data = {"_id": "env-id"}  # missing key
        env = EnvironmentMetadata.from_json(data)
        self.assertEqual(env.id, "env-id")
        self.assertEqual(env.key, "")  # default empty string


class TestConfigMetadata(unittest.TestCase):
    def test_config_metadata_creation(self):
        """Test ConfigMetadata constructs correctly with all data"""
        project = ProjectMetadata(id="proj-id", key="proj-key")
        environment = EnvironmentMetadata(id="env-id", key="env-key")
        
        metadata = ConfigMetadata(
            config_etag="etag-123",
            config_last_modified="2023-01-01T00:00:00Z",
            project=project,
            environment=environment
        )
        
        self.assertEqual(metadata.config_etag, "etag-123")
        self.assertEqual(metadata.config_last_modified, "2023-01-01T00:00:00Z")
        self.assertEqual(metadata.project, project)
        self.assertEqual(metadata.environment, environment)

    def test_config_metadata_from_config_response(self):
        """Test ConfigMetadata.from_config_response with complete data"""
        config_data = {
            "project": {"_id": "proj-id", "key": "proj-key"},
            "environment": {"_id": "env-id", "key": "env-key"}
        }
        
        metadata = ConfigMetadata.from_config_response(
            config_data,
            etag="etag-123",
            last_modified="2023-01-01T00:00:00Z"
        )
        
        self.assertEqual(metadata.config_etag, "etag-123")
        self.assertEqual(metadata.config_last_modified, "2023-01-01T00:00:00Z")
        self.assertIsNotNone(metadata.project)
        self.assertEqual(metadata.project.id, "proj-id")
        self.assertEqual(metadata.project.key, "proj-key")
        self.assertIsNotNone(metadata.environment)
        self.assertEqual(metadata.environment.id, "env-id")
        self.assertEqual(metadata.environment.key, "env-key")

    def test_config_metadata_from_config_response_missing_data(self):
        """Test ConfigMetadata.from_config_response handles missing data gracefully"""
        config_data = {}  # empty config data
        
        metadata = ConfigMetadata.from_config_response(
            config_data,
            etag=None,
            last_modified=None
        )
        
        self.assertIsNone(metadata.config_etag)
        self.assertIsNone(metadata.config_last_modified)
        self.assertIsNone(metadata.project)
        self.assertIsNone(metadata.environment)

    def test_config_metadata_from_config_response_partial_data(self):
        """Test ConfigMetadata.from_config_response with partial data"""
        config_data = {
            "project": {"_id": "proj-id", "key": "proj-key"}
            # missing environment
        }
        
        metadata = ConfigMetadata.from_config_response(
            config_data,
            etag="etag-123",
            last_modified="2023-01-01T00:00:00Z"
        )
        
        self.assertEqual(metadata.config_etag, "etag-123")
        self.assertEqual(metadata.config_last_modified, "2023-01-01T00:00:00Z")
        self.assertIsNotNone(metadata.project)
        self.assertIsNone(metadata.environment)

    def test_config_metadata_string_representation(self):
        """Test ConfigMetadata string representation"""
        project = ProjectMetadata(id="proj-id", key="proj-key")
        environment = EnvironmentMetadata(id="env-id", key="env-key")
        
        metadata = ConfigMetadata(
            config_etag="etag-123",
            config_last_modified="2023-01-01T00:00:00Z",
            project=project,
            environment=environment
        )
        
        str_repr = str(metadata)
        self.assertIn("etag=etag-123", str_repr)
        self.assertIn("last_modified=2023-01-01T00:00:00Z", str_repr)
        self.assertIn("project=", str_repr)
        self.assertIn("environment=", str_repr)


class TestHookContextMetadata(unittest.TestCase):
    def setUp(self):
        self.user = DevCycleUser(user_id="test-user")
        self.project = ProjectMetadata(id="proj-id", key="proj-key")
        self.environment = EnvironmentMetadata(id="env-id", key="env-key")
        self.metadata = ConfigMetadata(
            config_etag="etag-123",
            config_last_modified="2023-01-01T00:00:00Z",
            project=self.project,
            environment=self.environment
        )

    def test_hook_context_with_metadata(self):
        """Test HookContext with metadata"""
        context = HookContext("test-key", self.user, "default-value", self.metadata)
        
        self.assertEqual(context.key, "test-key")
        self.assertEqual(context.user, self.user)
        self.assertEqual(context.default_value, "default-value")
        self.assertEqual(context.metadata, self.metadata)

    def test_hook_context_without_metadata(self):
        """Test HookContext without metadata (cloud client case)"""
        context = HookContext("test-key", self.user, "default-value", metadata=None)
        
        self.assertEqual(context.key, "test-key")
        self.assertEqual(context.user, self.user)
        self.assertEqual(context.default_value, "default-value")
        self.assertIsNone(context.metadata)

    def test_hook_context_get_metadata(self):
        """Test HookContext.get_metadata method"""
        context = HookContext("test-key", self.user, "default-value", self.metadata)
        
        retrieved_metadata = context.get_metadata()
        self.assertEqual(retrieved_metadata, self.metadata)
        self.assertEqual(retrieved_metadata.config_etag, "etag-123")
        self.assertEqual(retrieved_metadata.project.id, "proj-id")

    def test_hook_context_get_metadata_none(self):
        """Test HookContext.get_metadata returns None when no metadata"""
        context = HookContext("test-key", self.user, "default-value", metadata=None)
        
        retrieved_metadata = context.get_metadata()
        self.assertIsNone(retrieved_metadata)


class TestConfigMetadataIntegration(unittest.TestCase):
    """Integration tests for config metadata functionality"""
    
    def test_metadata_flow_in_hooks(self):
        """Test that metadata flows correctly through hook execution stages"""
        # This test would require a more complex setup with actual hook execution
        # For now, we'll test the basic structure
        user = DevCycleUser(user_id="test-user")
        metadata = ConfigMetadata(
            config_etag="etag-123",
            config_last_modified="2023-01-01T00:00:00Z",
            project=ProjectMetadata(id="proj-id", key="proj-key"),
            environment=EnvironmentMetadata(id="env-id", key="env-key")
        )
        
        context = HookContext("test-key", user, "default-value", metadata)
        
        # Verify metadata is accessible in all hook stages
        self.assertIsNotNone(context.get_metadata())
        self.assertEqual(context.get_metadata().config_etag, "etag-123")
        self.assertEqual(context.get_metadata().project.key, "proj-key")
        self.assertEqual(context.get_metadata().environment.key, "env-key")

    def test_metadata_null_safety(self):
        """Test that metadata handling is null-safe"""
        user = DevCycleUser(user_id="test-user")
        
        # Test with None metadata (cloud client case)
        context = HookContext("test-key", user, "default-value", metadata=None)
        self.assertIsNone(context.get_metadata())
        
        # Test with empty metadata
        empty_metadata = ConfigMetadata(
            config_etag=None,
            config_last_modified=None,
            project=None,
            environment=None
        )
        context = HookContext("test-key", user, "default-value", empty_metadata)
        retrieved_metadata = context.get_metadata()
        self.assertIsNotNone(retrieved_metadata)
        self.assertIsNone(retrieved_metadata.config_etag)
        self.assertIsNone(retrieved_metadata.project)
        self.assertIsNone(retrieved_metadata.environment)


if __name__ == "__main__":
    unittest.main()