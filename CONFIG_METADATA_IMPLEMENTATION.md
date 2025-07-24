# Config Metadata Implementation

This document describes the implementation of config metadata functionality for the DevCycle Python SDK, based on the [Java SDK implementation in PR #178](https://github.com/DevCycleHQ/java-server-sdk/pull/178).

## 🎯 Overview

The config metadata feature adds project information, environment details, and config versioning to the local SDK evaluation context, making it accessible to evaluation hooks for enhanced debugging and monitoring capabilities.

## 📋 Implementation Summary

### ✅ Core Requirements Met

1. **New Data Models Created**
   - `ConfigMetadata` - Contains project, environment, and versioning information
   - `ProjectMetadata` - Project information (id, key)
   - `EnvironmentMetadata` - Environment information (id, key)

2. **HookContext Updated**
   - Added `metadata: Optional[ConfigMetadata]` parameter
   - Added `get_metadata()` method for accessing metadata
   - Maintains backward compatibility with optional parameter

3. **Configuration Manager Enhanced**
   - `EnvironmentConfigManager` now stores config metadata
   - Added `get_config_metadata()` method
   - Metadata created from API response headers and data

4. **Client Interface Updated**
   - `DevCycleLocalClient` exposes metadata via `get_metadata()` method
   - Local client passes metadata to HookContext in variable evaluation
   - `DevCycleCloudClient` passes null metadata (maintains distinction)

5. **JSON Serialization Centralized**
   - Created `JSONUtils` class for consistent serialization
   - Handles unknown properties gracefully for API compatibility
   - Separate configurations for config vs events

## 🏗️ Architecture

### Data Flow

```
Config API Response → Extract Headers & Data → Create Metadata → Store in Manager → Pass to Hooks
```

### Key Components

1. **ConfigMetadata** (`devcycle_python_sdk/models/config_metadata.py`)
   - Contains ETag, Last-Modified, project, and environment information
   - Factory method `from_config_response()` for easy creation from API data

2. **HookContext** (`devcycle_python_sdk/models/eval_hook_context.py`)
   - Updated to include optional metadata parameter
   - Provides `get_metadata()` method for hook access

3. **EnvironmentConfigManager** (`devcycle_python_sdk/managers/config_manager.py`)
   - Stores config metadata as instance variable
   - Creates metadata from API response
   - Exposes metadata via `get_config_metadata()`

4. **DevCycleLocalClient** (`devcycle_python_sdk/local_client.py`)
   - Exposes metadata via `get_metadata()` method
   - Passes metadata to HookContext in variable evaluation

5. **DevCycleCloudClient** (`devcycle_python_sdk/cloud_client.py`)
   - Passes null metadata to HookContext (maintains separation)

6. **JSONUtils** (`devcycle_python_sdk/util/json_utils.py`)
   - Centralized JSON serialization/deserialization
   - Handles unknown properties gracefully
   - Consistent behavior across SDK

## 🔧 Usage Examples

### Accessing Metadata in Local Client

```python
from devcycle_python_sdk import DevCycleLocalClient, DevCycleLocalOptions

client = DevCycleLocalClient("server-sdk-key", DevCycleLocalOptions())

# Get current config metadata
metadata = client.get_metadata()
if metadata:
    print(f"Project: {metadata.project.key}")
    print(f"Environment: {metadata.environment.key}")
    print(f"Config ETag: {metadata.config_etag}")
    print(f"Last Modified: {metadata.config_last_modified}")
```

### Using Metadata in Evaluation Hooks

```python
from devcycle_python_sdk.models.eval_hook import EvalHook
from devcycle_python_sdk.models.eval_hook_context import HookContext

class MyEvalHook(EvalHook):
    def before(self, context: HookContext):
        metadata = context.get_metadata()
        if metadata:
            print(f"Evaluating variable {context.key} for project {metadata.project.key}")
        return context
    
    def after(self, context: HookContext, variable):
        metadata = context.get_metadata()
        if metadata:
            print(f"Variable {context.key} evaluated in environment {metadata.environment.key}")
    
    def error(self, context: HookContext, error):
        metadata = context.get_metadata()
        if metadata:
            print(f"Error evaluating {context.key} in project {metadata.project.key}")
    
    def on_finally(self, context: HookContext, variable):
        metadata = context.get_metadata()
        if metadata:
            print(f"Completed evaluation for {context.key}")

# Add hook to client
client.add_hook(MyEvalHook())
```

### Cloud vs Local Client Distinction

```python
# Local client - has metadata
local_client = DevCycleLocalClient("server-sdk-key", DevCycleLocalOptions())
metadata = local_client.get_metadata()  # Returns ConfigMetadata or None

# Cloud client - no metadata (uses external API)
cloud_client = DevCycleCloudClient("server-sdk-key", DevCycleCloudOptions())
# cloud_client.get_metadata() would return None (not implemented for cloud)
```

## 🧪 Testing

### Test Coverage

The implementation includes comprehensive test coverage:

1. **Unit Tests** (`test/test_config_metadata.py`)
   - Metadata creation and serialization
   - HookContext integration
   - Null safety and edge cases

2. **Integration Tests** (`test/test_client_metadata.py`)
   - Local client metadata functionality
   - Cloud client null metadata
   - Config manager metadata creation

3. **Standalone Tests** (`test_metadata_standalone.py`)
   - Complete functionality verification
   - No external dependencies required

### Running Tests

```bash
# Run standalone tests (no dependencies required)
python3 test_metadata_standalone.py

# Run unit tests (requires test dependencies)
python3 -m pytest test/test_config_metadata.py -v

# Run integration tests
python3 -m pytest test/test_client_metadata.py -v
```

## 🔍 Key Features

### 1. Null Safety
- All metadata fields are optional
- Graceful handling of missing API data
- Cloud client passes null metadata

### 2. Backward Compatibility
- HookContext metadata parameter is optional
- Existing code continues to work unchanged
- No breaking changes to public API

### 3. API Evolution Support
- JSONUtils handles unknown properties gracefully
- Configurable serialization for different use cases
- Robust error handling for malformed responses

### 4. Clear Client Distinction
- Local client: populated metadata from config API
- Cloud client: null metadata (uses external API)
- Maintains separation of concerns

## 📊 Success Criteria Met

- ✅ Config metadata accessible via `client.get_metadata()`
- ✅ Metadata available in all evaluation hooks
- ✅ Local client populates metadata, cloud client uses null
- ✅ Robust error handling and null safety
- ✅ Comprehensive test coverage
- ✅ Consistent JSON serialization behavior

## 🔗 Files Modified

### New Files
- `devcycle_python_sdk/models/config_metadata.py` - Metadata data models
- `devcycle_python_sdk/util/json_utils.py` - Centralized JSON utilities
- `test/test_config_metadata.py` - Unit tests
- `test/test_client_metadata.py` - Integration tests
- `test_metadata_standalone.py` - Standalone verification tests

### Modified Files
- `devcycle_python_sdk/models/eval_hook_context.py` - Added metadata support
- `devcycle_python_sdk/managers/config_manager.py` - Added metadata storage
- `devcycle_python_sdk/local_client.py` - Added metadata exposure
- `devcycle_python_sdk/cloud_client.py` - Added null metadata
- `devcycle_python_sdk/api/config_client.py` - Added JSON utility usage
- `devcycle_python_sdk/models/__init__.py` - Exported new classes

## 🎯 Benefits

1. **Enhanced Debugging**: Hooks can access project/environment context
2. **Better Monitoring**: Config versioning information available
3. **API Compatibility**: Graceful handling of API evolution
4. **Clear Separation**: Local vs cloud client distinction maintained
5. **Backward Compatibility**: No breaking changes to existing code

## 🔮 Future Enhancements

1. **Cloud Client Metadata**: Could add metadata support for cloud client if needed
2. **Extended Metadata**: Could include additional config information
3. **Caching**: Could add metadata caching for performance
4. **Validation**: Could add metadata validation for data integrity

---

**Goal Achieved**: Enhanced debugging capabilities by providing evaluation context about which project/environment configuration is being used, along with versioning information for troubleshooting configuration-related issues.