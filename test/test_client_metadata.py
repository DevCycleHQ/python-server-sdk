import unittest
from unittest.mock import Mock, patch, MagicMock
import json

from devcycle_python_sdk import DevCycleLocalOptions, DevCycleCloudOptions
from devcycle_python_sdk.local_client import DevCycleLocalClient
from devcycle_python_sdk.cloud_client import DevCycleCloudClient
from devcycle_python_sdk.models.config_metadata import ConfigMetadata, ProjectMetadata, EnvironmentMetadata
from devcycle_python_sdk.models.user import DevCycleUser


class TestLocalClientMetadata(unittest.TestCase):
    """Test metadata functionality in local client"""
    
    def setUp(self):
        self.sdk_key = "server-test-key"
        self.options = DevCycleLocalOptions()
        self.user = DevCycleUser(user_id="test-user")

    @patch('devcycle_python_sdk.managers.config_manager.EnvironmentConfigManager')
    @patch('devcycle_python_sdk.api.local_bucketing.LocalBucketing')
    def test_local_client_get_metadata_initialized(self, mock_bucketing, mock_config_manager):
        """Test that local client returns metadata when initialized"""
        # Mock the config manager to return metadata
        mock_metadata = ConfigMetadata(
            config_etag="etag-123",
            config_last_modified="2023-01-01T00:00:00Z",
            project=ProjectMetadata(id="proj-id", key="proj-key"),
            environment=EnvironmentMetadata(id="env-id", key="env-key")
        )
        
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.is_initialized.return_value = True
        mock_config_manager_instance.get_config_metadata.return_value = mock_metadata
        mock_config_manager.return_value = mock_config_manager_instance
        
        client = DevCycleLocalClient(self.sdk_key, self.options)
        
        # Test get_metadata method
        metadata = client.get_metadata()
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.config_etag, "etag-123")
        self.assertEqual(metadata.project.key, "proj-key")
        self.assertEqual(metadata.environment.key, "env-key")

    @patch('devcycle_python_sdk.managers.config_manager.EnvironmentConfigManager')
    @patch('devcycle_python_sdk.api.local_bucketing.LocalBucketing')
    def test_local_client_get_metadata_not_initialized(self, mock_bucketing, mock_config_manager):
        """Test that local client returns None metadata when not initialized"""
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.is_initialized.return_value = False
        mock_config_manager_instance.get_config_metadata.return_value = None
        mock_config_manager.return_value = mock_config_manager_instance
        
        client = DevCycleLocalClient(self.sdk_key, self.options)
        
        # Test get_metadata method
        metadata = client.get_metadata()
        self.assertIsNone(metadata)

    @patch('devcycle_python_sdk.managers.config_manager.EnvironmentConfigManager')
    @patch('devcycle_python_sdk.api.local_bucketing.LocalBucketing')
    def test_local_client_variable_with_metadata(self, mock_bucketing, mock_config_manager):
        """Test that local client passes metadata to HookContext in variable evaluation"""
        # Mock the config manager
        mock_metadata = ConfigMetadata(
            config_etag="etag-123",
            config_last_modified="2023-01-01T00:00:00Z",
            project=ProjectMetadata(id="proj-id", key="proj-key"),
            environment=EnvironmentMetadata(id="env-id", key="env-key")
        )
        
        mock_config_manager_instance = Mock()
        mock_config_manager_instance.is_initialized.return_value = True
        mock_config_manager_instance.get_config_metadata.return_value = mock_metadata
        mock_config_manager.return_value = mock_config_manager_instance
        
        # Mock the bucketing to return a variable
        mock_bucketing_instance = Mock()
        mock_bucketing_instance.get_variable_for_user_protobuf.return_value = None
        mock_bucketing.return_value = mock_bucketing_instance
        
        client = DevCycleLocalClient(self.sdk_key, self.options)
        
        # Mock the eval hooks manager to capture the context
        captured_context = None
        original_run_before = client.eval_hooks_manager.run_before
        
        def mock_run_before(context):
            nonlocal captured_context
            captured_context = context
            return None
        
        client.eval_hooks_manager.run_before = mock_run_before
        
        # Call variable method
        client.variable(self.user, "test-key", "default-value")
        
        # Verify that metadata was passed to HookContext
        self.assertIsNotNone(captured_context)
        self.assertEqual(captured_context.key, "test-key")
        self.assertEqual(captured_context.user, self.user)
        self.assertEqual(captured_context.default_value, "default-value")
        self.assertEqual(captured_context.metadata, mock_metadata)


class TestCloudClientMetadata(unittest.TestCase):
    """Test metadata functionality in cloud client"""
    
    def setUp(self):
        self.sdk_key = "server-test-key"
        self.options = DevCycleCloudOptions()
        self.user = DevCycleUser(user_id="test-user")

    @patch('devcycle_python_sdk.api.bucketing_client.BucketingAPIClient')
    def test_cloud_client_variable_with_null_metadata(self, mock_bucketing_api):
        """Test that cloud client passes null metadata to HookContext"""
        # Mock the bucketing API
        mock_bucketing_instance = Mock()
        mock_bucketing_instance.variable.return_value = Mock()
        mock_bucketing_api.return_value = mock_bucketing_instance
        
        client = DevCycleCloudClient(self.sdk_key, self.options)
        
        # Mock the eval hooks manager to capture the context
        captured_context = None
        original_run_before = client.eval_hooks_manager.run_before
        
        def mock_run_before(context):
            nonlocal captured_context
            captured_context = context
            return None
        
        client.eval_hooks_manager.run_before = mock_run_before
        
        # Call variable method
        client.variable(self.user, "test-key", "default-value")
        
        # Verify that null metadata was passed to HookContext
        self.assertIsNotNone(captured_context)
        self.assertEqual(captured_context.key, "test-key")
        self.assertEqual(captured_context.user.user_id, "test-user")
        self.assertEqual(captured_context.default_value, "default-value")
        self.assertIsNone(captured_context.metadata)  # Cloud client should have null metadata


class TestConfigManagerMetadata(unittest.TestCase):
    """Test config manager metadata functionality"""
    
    def setUp(self):
        self.sdk_key = "server-test-key"
        self.options = DevCycleLocalOptions()

    @patch('devcycle_python_sdk.api.config_client.ConfigAPIClient')
    @patch('devcycle_python_sdk.api.local_bucketing.LocalBucketing')
    def test_config_manager_metadata_creation(self, mock_bucketing, mock_config_client):
        """Test that config manager creates and stores metadata correctly"""
        # Mock config API response
        config_data = {
            "project": {"_id": "proj-id", "key": "proj-key"},
            "environment": {"_id": "env-id", "key": "env-key"}
        }
        
        mock_config_client_instance = Mock()
        mock_config_client_instance.get_config.return_value = (
            config_data, "etag-123", "2023-01-01T00:00:00Z"
        )
        mock_config_client.return_value = mock_config_client_instance
        
        # Mock bucketing
        mock_bucketing_instance = Mock()
        mock_bucketing.return_value = mock_bucketing_instance
        
        from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
        
        config_manager = EnvironmentConfigManager(self.sdk_key, self.options, mock_bucketing_instance)
        
        # Simulate config fetch
        config_manager._get_config()
        
        # Verify metadata was created and stored
        metadata = config_manager.get_config_metadata()
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.config_etag, "etag-123")
        self.assertEqual(metadata.config_last_modified, "2023-01-01T00:00:00Z")
        self.assertIsNotNone(metadata.project)
        self.assertEqual(metadata.project.id, "proj-id")
        self.assertEqual(metadata.project.key, "proj-key")
        self.assertIsNotNone(metadata.environment)
        self.assertEqual(metadata.environment.id, "env-id")
        self.assertEqual(metadata.environment.key, "env-key")

    @patch('devcycle_python_sdk.api.config_client.ConfigAPIClient')
    @patch('devcycle_python_sdk.api.local_bucketing.LocalBucketing')
    def test_config_manager_metadata_no_config(self, mock_bucketing, mock_config_client):
        """Test that config manager handles no config gracefully"""
        # Mock config API to return no config
        mock_config_client_instance = Mock()
        mock_config_client_instance.get_config.return_value = (None, None, None)
        mock_config_client.return_value = mock_config_client_instance
        
        # Mock bucketing
        mock_bucketing_instance = Mock()
        mock_bucketing.return_value = mock_bucketing_instance
        
        from devcycle_python_sdk.managers.config_manager import EnvironmentConfigManager
        
        config_manager = EnvironmentConfigManager(self.sdk_key, self.options, mock_bucketing_instance)
        
        # Simulate config fetch
        config_manager._get_config()
        
        # Verify metadata is None when no config
        metadata = config_manager.get_config_metadata()
        self.assertIsNone(metadata)


class TestJSONUtils(unittest.TestCase):
    """Test JSON utility functionality"""
    
    def test_json_utils_serialize_config(self):
        """Test JSONUtils.serialize_config"""
        from devcycle_python_sdk.util.json_utils import JSONUtils
        
        data = {"key": "value", "number": 123, "boolean": True}
        serialized = JSONUtils.serialize_config(data)
        
        # Should be valid JSON
        parsed = json.loads(serialized)
        self.assertEqual(parsed["key"], "value")
        self.assertEqual(parsed["number"], 123)
        self.assertEqual(parsed["boolean"], True)

    def test_json_utils_deserialize_config(self):
        """Test JSONUtils.deserialize_config"""
        from devcycle_python_sdk.util.json_utils import JSONUtils
        
        json_str = '{"key": "value", "number": 123}'
        deserialized = JSONUtils.deserialize_config(json_str)
        
        self.assertEqual(deserialized["key"], "value")
        self.assertEqual(deserialized["number"], 123)

    def test_json_utils_deserialize_config_invalid_json(self):
        """Test JSONUtils.deserialize_config with invalid JSON"""
        from devcycle_python_sdk.util.json_utils import JSONUtils
        
        invalid_json = '{"key": "value", "number": 123'  # Missing closing brace
        
        with self.assertRaises(ValueError):
            JSONUtils.deserialize_config(invalid_json)

    def test_json_utils_safe_get(self):
        """Test JSONUtils.safe_get"""
        from devcycle_python_sdk.util.json_utils import JSONUtils
        
        data = {"key": "value", "nested": {"inner": "data"}}
        
        # Test existing key
        self.assertEqual(JSONUtils.safe_get(data, "key"), "value")
        
        # Test missing key with default
        self.assertEqual(JSONUtils.safe_get(data, "missing", "default"), "default")
        
        # Test missing key without default
        self.assertIsNone(JSONUtils.safe_get(data, "missing"))

    def test_json_utils_safe_get_nested(self):
        """Test JSONUtils.safe_get_nested"""
        from devcycle_python_sdk.util.json_utils import JSONUtils
        
        data = {"level1": {"level2": {"level3": "value"}}}
        
        # Test existing nested path
        self.assertEqual(JSONUtils.safe_get_nested(data, "level1", "level2", "level3"), "value")
        
        # Test missing nested path
        self.assertIsNone(JSONUtils.safe_get_nested(data, "level1", "level2", "missing"))
        
        # Test with default
        self.assertEqual(
            JSONUtils.safe_get_nested(data, "level1", "level2", "missing", default="default"),
            "default"
        )


if __name__ == "__main__":
    unittest.main()