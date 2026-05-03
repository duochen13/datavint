# Architectural Decisions

## Session Management

- Using gstack `/context-save` and `/context-restore` for session continuity
- Checkpoint mode: explicit (not continuous auto-commits)
- Skill routing: not yet configured in CLAUDE.md

## Data Validation Architecture

- Following TFDV (TensorFlow Data Validation) functional API design
- Schema detector split into modular components:
  - Type detection
  - Range detection
  - Separate orchestration layer
