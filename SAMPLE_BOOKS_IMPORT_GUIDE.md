# 📚 Sample Books Import Guide for NTA Library

## 📋 Import File Format

Your Django admin uses **django-import-export** which supports multiple formats:
- **Excel (.xlsx, .xls)**
- **CSV (.csv)**
- **JSON (.json)**
- **YAML (.yaml)**

## 📊 Sample Data Files Created

### 1. CSV Format
**File**: `sample_books_import.csv`
- Ready to use for import
- Contains 10 sample books with realistic data
- All required and optional fields included

### 2. Excel Format Instructions
To create an Excel file:
1. Open the `sample_books_import.csv` in Excel
2. Save as `.xlsx` format
3. Use the Excel file for import

## 🔧 Field Mapping Guide

### Required Fields (Must be included)
| Field | Description | Example |
|-------|-------------|----------|
| `serial` | Unique book identifier | BK001 |
| `shelf` | Physical location | A1-01 |
| `title` | Book title | "The Great Gatsby" |
| `author` | Primary author(s) | "F. Scott Fitzgerald" |

### Optional Fields
| Field | Description | Format/Options |
|-------|-------------|----------------|
| `isbn` | ISBN-13 number | 9780743273565 |
| `barcode` | Barcode for scanning | 123456789012 |
| `publisher` | Publishing company | "Scribner" |
| `publication_date` | Publication date | YYYY-MM-DD (1925-04-10) |
| `edition` | Book edition | "First Edition" |
| `pages` | Number of pages | 180 |
| `language` | Language code | en, ar, fr, es, de, other |
| `dewey_code` | Dewey classification | 813.52 |
| `cover_type` | Cover type | paperback, hardcover, spiral, digital |
| `condition` | Book condition | excellent, good, fair, poor, damaged |
| `is_available` | Availability status | true, false |

### Classification Fields
| Field | Description |
|-------|-------------|
| `main_class` | Main subject classification |
| `divisions` | Subject divisions |
| `sections` | Subject sections |
| `cutter_author` | Cutter number for author |

### Additional Information
| Field | Description |
|-------|-------------|
| `volume` | Volume number |
| `series` | Book series name |
| `editor` | Editor name |
| `translator` | Translator name |
| `place_of_publication` | Publication location |
| `website` | Related website URL |
| `source` | How book was acquired |
| `book_summary` | Brief description |
| `contents` | Table of contents |
| `keywords` | Comma-separated keywords |

## 📝 Import Instructions

### Step 1: Prepare Your Data
1. Use the sample CSV as a template
2. Replace sample data with your actual books
3. Ensure required fields are filled
4. Save as Excel (.xlsx) or keep as CSV

### Step 2: Import Process
1. Go to: `http://127.0.0.1:8000/admin/books/book/`
2. Click **"Import"** button
3. Choose your file (Excel/CSV)
4. Review the preview
5. Click **"Confirm import"**

### Step 3: Validation
- Check for any error messages
- Verify imported books in the admin
- Ensure unique fields (serial, ISBN, barcode) don't conflict

## ⚠️ Important Notes

### Data Validation
- **Serial numbers** must be unique
- **ISBN** must be unique (if provided)
- **Barcode** must be unique (if provided)
- **Pages** must be positive numbers
- **Dates** must be in YYYY-MM-DD format

### Choice Fields
- **Language**: en, ar, fr, es, de, other
- **Cover Type**: paperback, hardcover, spiral, digital
- **Condition**: excellent, good, fair, poor, damaged
- **Boolean Fields**: true/false (case-sensitive)

### Text Fields
- Use quotes for fields containing commas
- Keep within character limits:
  - Title: 500 characters
  - Author: 500 characters
  - Publisher: 200 characters
  - Serial: 20 characters
  - Shelf: 20 characters

## 🔄 Sample Data Overview

The sample file includes:
1. **Classic Literature** (Gatsby, Mockingbird, 1984, Pride & Prejudice)
2. **Technical Books** (Python Programming)
3. **Science** (Brief History of Time)
4. **Philosophy/Strategy** (Art of War, The Alchemist)
5. **History** (Sapiens)
6. **Coming of Age** (Catcher in the Rye)

Each entry demonstrates:
- Proper field formatting
- Realistic library data
- Different book types and genres
- Various publication dates and editions
- Different physical conditions
- Proper Dewey classification

## 🚀 Quick Start

1. **Download**: Use `sample_books_import.csv`
2. **Convert**: Open in Excel, save as `.xlsx`
3. **Import**: Upload to admin import page
4. **Verify**: Check imported books in admin

**Ready to import!** 📚✨