# Frontend Changes

This document outlines various features and tools that have been added to the Course Materials RAG System project.

---

## 1. Code Quality Tools Implementation

### Overview
This section documents the code quality tools that have been added to the development workflow.

### Changes Made

#### 1.1. Dependencies Added
Added three essential code quality tools to `pyproject.toml`:
- **black** (>=24.0.0): Automatic code formatter
- **flake8** (>=7.0.0): Code linter for style and error checking
- **isort** (>=5.13.0): Import statement organizer

#### 1.2. Configuration Files

**pyproject.toml:**
Added configuration sections for black and isort:

**Black Configuration:**
- Line length: 88 characters (Python standard)
- Target version: Python 3.13
- Excludes: .venv, build, dist, chroma_db

**isort Configuration:**
- Profile: black (ensures compatibility)
- Line length: 88 characters
- Multi-line output style: 3 (vertical hanging indent)
- Excludes: .venv, chroma_db

**.flake8:**
Created dedicated flake8 configuration file:
- Max line length: 88 characters
- Ignored rules: E203, E266, E501, W503 (black compatibility)
- Max complexity: 10
- Per-file ignores:
  - Test files: F401 (unused imports), F841 (unused variables)
  - document_processor.py: C901 (complexity)
  - app.py: E402 (module level imports)

#### 1.3. Development Scripts

Created three executable shell scripts for code quality management:

**format.sh:**
Automatically formats all Python code:
```bash
./format.sh
```
- Runs isort to organize imports
- Runs black to format code
- Makes code consistent across the entire codebase

**lint.sh:**
Checks code quality without making changes:
```bash
./lint.sh
```
- Runs flake8 on backend/ and main.py
- Reports style issues and potential errors
- Exits with error code if issues found

**check-quality.sh:**
Comprehensive quality check suite:
```bash
./check-quality.sh
```
- Checks black formatting (dry run)
- Checks isort organization (dry run)
- Runs flake8 linter
- Provides detailed summary of all checks
- Exits with error if any check fails

#### 1.4. Code Formatting Applied
All Python files in the codebase have been formatted:
- 14 files reformatted with black
- 13 files fixed with isort
- All import statements properly organized
- Consistent code style throughout

#### 1.5. Import Cleanup
Removed unused imports from multiple files:
- `backend/models.py`: Removed unused `Dict` import
- `backend/rag_system.py`: Removed unused `CourseChunk` and `Lesson` imports
- `backend/search_tools.py`: Removed unused `Protocol` import
- `backend/vector_store.py`: Removed unused `SentenceTransformer` import
- `backend/app.py`: Removed unused `Path` import, consolidated duplicate imports

### Usage Guidelines

**Before Committing Code:**
Always run the quality check script before committing:
```bash
./check-quality.sh
```

**Formatting Code:**
To automatically format code after making changes:
```bash
./format.sh
```

**Checking Specific Issues:**
To only check linting issues:
```bash
./lint.sh
```

### Benefits

1. **Consistency**: All code follows the same formatting standards
2. **Readability**: Properly formatted code is easier to read and maintain
3. **Error Prevention**: Flake8 catches common errors and code smells
4. **Automation**: Scripts make it easy to maintain code quality
5. **CI/CD Ready**: Scripts can be integrated into continuous integration pipelines

### Tool Versions
- black: 25.9.0 (installed)
- flake8: 7.3.0 (installed)
- isort: 7.0.0 (installed)

### Next Steps

Consider adding these scripts to:
1. Pre-commit hooks (automatically run before git commits)
2. CI/CD pipeline (GitHub Actions, GitLab CI, etc.)
3. IDE integration (VS Code, PyCharm settings)

---

## 2. Theme Toggle Feature

### Overview
Added a theme toggle button that allows users to switch between dark and light themes with smooth transitions and persistent preference storage.

### Files Modified

#### 2.1. `frontend/index.html`
- **Added**: Theme toggle button with sun and moon icons positioned at the top-right of the page
- **Location**: Lines 13-29
- **Features**:
  - Accessible with `aria-label` and `title` attributes
  - SVG icons for sun (light mode) and moon (dark mode)
  - Keyboard navigable button

#### 2.2. `frontend/style.css`
- **Added**: CSS variables for both dark and light themes (Lines 8-45)
  - Dark theme (default): Uses existing dark color scheme
  - Light theme: New color palette with light backgrounds and dark text
  - Includes `--code-bg` variable for code block backgrounds

- **Updated**: Body element to include smooth transitions (Line 57)
  - Added `transition: background-color 0.3s ease, color 0.3s ease;`

- **Updated**: Code block styling to use CSS variables (Lines 355-369)
  - Changed hardcoded `rgba(0, 0, 0, 0.2)` to `var(--code-bg)`
  - Ensures proper code block appearance in both themes

- **Added**: Theme toggle button styles (Lines 766-828)
  - Fixed positioning in top-right corner
  - Circular button with smooth hover and active states
  - Rotating icon animation on theme switch
  - Responsive sizing for mobile devices
  - Accessible focus states

#### 2.3. `frontend/script.js`
- **Added**: Theme management system with three new functions:

  1. **`initializeTheme()`** (Lines 243-247)
     - Checks localStorage for saved theme preference
     - Defaults to dark theme if no preference saved
     - Called on page load

  2. **`toggleTheme()`** (Lines 249-253)
     - Switches between light and dark themes
     - Called when toggle button is clicked

  3. **`setTheme(theme)`** (Lines 255-265)
     - Applies the theme by setting `data-theme` attribute on document root
     - Saves preference to localStorage
     - Updates button accessibility labels

- **Updated**: DOM elements initialization (Line 8)
  - Added `themeToggle` to global variables

- **Updated**: `setupEventListeners()` function (Lines 29-30, 42-47)
  - Added click listener for theme toggle button
  - Added keyboard navigation support (Enter and Space keys)

### Features Implemented

#### 2.4. Toggle Button Design ✓
- Icon-based design with sun/moon SVG icons
- Positioned in top-right corner (fixed position)
- Smooth rotation and scale animation on hover
- Smooth icon transition when switching themes
- Accessible and keyboard-navigable

#### 2.5. Light Theme CSS Variables ✓
- Light background colors (`--background: #f8fafc`)
- Dark text for contrast (`--text-primary: #0f172a`)
- Adjusted surface colors (`--surface: #ffffff`)
- Proper border colors (`--border-color: #e2e8f0`)
- Maintains good accessibility standards

#### 2.6. JavaScript Functionality ✓
- Toggle between themes on button click
- Smooth 0.3s transitions for background and text colors
- LocalStorage persistence (theme preference saved)
- Automatic theme restoration on page reload

#### 2.7. Implementation Details ✓
- Uses CSS custom properties (CSS variables) for theme switching
- `data-theme` attribute on `<html>` element controls theme
- All existing elements work in both themes
- Maintains current visual hierarchy and design language
- Responsive design adjustments for mobile devices

## Color Palettes

### Dark Theme (Default)
- Background: `#0f172a`
- Surface: `#1e293b`
- Text Primary: `#f1f5f9`
- Text Secondary: `#94a3b8`
- Border: `#334155`
- Code Background: `rgba(0, 0, 0, 0.2)`

### Light Theme
- Background: `#f8fafc`
- Surface: `#ffffff`
- Text Primary: `#0f172a`
- Text Secondary: `#64748b`
- Border: `#e2e8f0`
- Code Background: `#f1f5f9`

## User Experience Enhancements

1. **Smooth Transitions**: 0.3s ease transitions on all color changes
2. **Persistent Preference**: Theme choice saved to localStorage
3. **Animated Icons**: Sun/moon icons rotate and scale during transition
4. **Hover Feedback**: Button rotates 15° and scales up on hover
5. **Keyboard Accessible**: Fully navigable with Tab, Enter, and Space keys
6. **Proper Focus States**: Clear focus ring for keyboard navigation
7. **Mobile Responsive**: Smaller button size on mobile devices

## Testing Recommendations

To test the theme toggle feature:

1. Load the application in a browser
2. Click the theme toggle button in the top-right corner
3. Verify smooth transition between dark and light themes
4. Test keyboard navigation (Tab to button, press Enter/Space)
5. Refresh the page and verify theme preference is maintained
6. Test on mobile viewport (button should be slightly smaller)
7. Verify all UI elements are readable in both themes:
   - Chat messages (user and assistant)
   - Sidebar elements
   - Input fields and buttons
   - Code blocks in messages
   - Source links
   - Collapsible sections

## Browser Compatibility

- Uses standard CSS custom properties (supported in all modern browsers)
- localStorage API (widely supported)
- SVG icons (universal support)
- CSS transitions and transforms (standard support)
- No vendor prefixes required for targeted browsers