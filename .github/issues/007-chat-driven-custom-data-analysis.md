# Feature: Chat-Driven Custom Data Analysis

## Description
Enable users to provide their own data sources (CSV files or Kaggle links) through the chat interface, and automatically generate executable code in the Code Playground to analyze that data using DataVint SDK.

## User Story
As a user, I want to:
1. Upload a CSV file or paste a Kaggle dataset link in the chat box
2. Have DataVint automatically generate code to load and profile my data
3. See the generated code in the "Custom Code" tab
4. Click "Run" to execute the analysis on my custom dataset
5. View the profiling results and data quality issues

## Current State
- Code Playground only has pre-defined templates (e.g., Titanic dataset)
- Users cannot analyze their own datasets
- No chat integration with code generation

## Proposed Behavior

### User Flow
```
1. User uploads CSV or pastes Kaggle link in chat
   ↓
2. Chat validates the data source
   ↓
3. System generates Python code with:
   - datavint SDK import
   - Data loading code (from file or Kaggle)
   - Basic profiling commands
   ↓
4. Code appears in "Custom Code" tab
   ↓
5. User clicks "Run" to execute
   ↓
6. Results display in the playground
```

### Example Generated Code

**For CSV Upload:**
```python
import datavint as vint
import pandas as pd

# Load your uploaded dataset
df = pd.read_csv('user_uploaded_data.csv')

# Run comprehensive data quality checks
stats, issues = vint.profile(df)

# Display results
print(f"Dataset shape: {df.shape}")
print(f"Found {len(issues)} data quality issues")

stats, issues
```

**For Kaggle Link:**
```python
import datavint as vint
import pandas as pd

# Load dataset from Kaggle
# Note: Requires kaggle API credentials
df = pd.read_csv('https://www.kaggle.com/...')

# Run comprehensive data quality checks
stats, issues = vint.profile(df)

# Display results
print(f"Dataset shape: {df.shape}")
print(f"Found {len(issues)} data quality issues")

stats, issues
```

## Technical Requirements

### Backend (FastAPI)
- [ ] New endpoint: `POST /api/chat/upload-dataset`
  - Accept CSV file uploads (multipart/form-data)
  - Store temporarily on server
  - Return dataset metadata (shape, columns, preview)

- [ ] New endpoint: `POST /api/chat/generate-code`
  - Accept data source info (file path or Kaggle URL)
  - Generate Python code dynamically
  - Return executable code string

- [ ] Modify `POST /api/code/execute-template`
  - Support custom code execution (not just templates)
  - Handle uploaded CSV files
  - Add file cleanup after execution

### Frontend (Vue)
- [ ] Update ChatPanel.vue
  - Add file upload button (CSV only)
  - Add Kaggle link input field
  - Show upload progress/status
  - Display "Code generated!" message

- [ ] Update CodePlayground.vue
  - Add "Custom Code" tab alongside template dropdown
  - Support editable code (not just read-only templates)
  - Show generated code from chat
  - Enable "Run" button for custom code

- [ ] Add state management
  - Store uploaded file reference
  - Store generated code
  - Sync between chat and code playground

### Security & Validation
- [ ] File size limit (e.g., 10MB max)
- [ ] File type validation (CSV only)
- [ ] Kaggle link validation (regex pattern)
- [ ] Sanitize user input to prevent code injection
- [ ] Rate limiting on file uploads
- [ ] Temporary file cleanup (delete after 1 hour)

## UI Mockup

### Chat Box Enhancement
```
┌─────────────────────────────────────┐
│  Chat with DataVint                 │
├─────────────────────────────────────┤
│                                     │
│  [📎 Upload CSV] [🔗 Kaggle Link]  │
│                                     │
│  Type your message...               │
│                                     │
└─────────────────────────────────────┘
```

### Code Playground Tab Update
```
┌─────────────────────────────────────┐
│  [Templates ▾] | [Custom Code]      │
│                                     │
│  ┌─ Generated Code ──────────────┐ │
│  │ import datavint as vint       │ │
│  │ import pandas as pd           │ │
│  │ ...                            │ │
│  └────────────────────────────────┘ │
│                          [Run ▶]    │
└─────────────────────────────────────┘
```

## Success Criteria
- [ ] User can upload CSV and see generated code within 2 seconds
- [ ] Generated code is valid and executable
- [ ] Code execution returns correct profiling results
- [ ] File upload works for files up to 10MB
- [ ] Kaggle links are validated before code generation
- [ ] Error messages are clear and actionable

## Future Enhancements (Out of Scope for MVP)
- Support for Excel files (.xlsx)
- Support for database connections (PostgreSQL, MySQL)
- Support for S3/GCS URLs
- Persistent storage of user datasets
- Code editing and re-execution
- Multiple dataset comparison

## Priority
**High** - This is a core value proposition: making DataVint work on users' own data, not just demo datasets.

## Labels
`enhancement`, `feature`, `chat`, `code-playground`, `user-data`
