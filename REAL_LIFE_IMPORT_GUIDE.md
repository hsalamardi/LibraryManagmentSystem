# Real Life Excel Import Guide

## Overview

This guide explains how to import books from your existing Excel file structure (`Real_ife_sample.xlsx`) into the NTA Library Management System.

## Supported File Structure

The system now supports importing Excel files with the following column structure:

### Required Columns
- **ß** - Index/ID column
- **serial** - Book serial number (used as unique identifier)
- **shelf** - Shelf location
- **Title** - Book title
- **Author** - Book author

### Optional Columns
- **ISBN** - International Standard Book Number
- **Publisher** - Book publisher
- **Edition** - Book edition
- **Pages** - Number of pages
- **Language** - Book language
- **Dewey_Code** - Dewey Decimal Classification code
- **Main_Class** - Main classification
- **Divisions** - Classification divisions
- **Sections** - Classification sections
- **Cutter_Author** - Cutter author number
- **Volume** - Volume number
- **Series** - Book series
- **Editor** - Book editor
- **Translator** - Book translator
- **Place_of_Publication** - Place where book was published
- **website** - Related website
- **Source** - Source of the book
- **Cover_Type** - Type of cover (hardcover, paperback, etc.)
- **Condition** - Physical condition of the book
- **Copy** - Copy number
- **Book_Summary** - Book summary/description
- **Contents** - Table of contents
- **Keywords** - Keywords for searching
- **Publication_Datte** - Publication date (note: handles the typo in your file)

## Column Mapping

The system automatically maps your Excel columns to the database fields:

| Excel Column | Database Field | Notes |
|--------------|----------------|---------|
| Title | title | Required |
| Author | author | Required |
| ISBN | isbn | Optional |
| Publisher | publisher | Optional |
| Edition | edition | Optional |
| Pages | pages | Optional |
| Language | language | Optional |
| Dewey_Code | dewey_code | Optional |
| Main_Class | main_class | Optional |
| Divisions | divisions | Optional |
| Sections | sections | Optional |
| Cutter_Author | cutter_author | Optional |
| Volume | volume | Optional |
| Series | series | Optional |
| Editor | editor | Optional |
| Translator | translator | Optional |
| Place_of_Publication | place_of_publication | Optional |
| website | website | Optional |
| Source | source | Optional |
| Cover_Type | cover_type | Optional |
| Condition | condition | Optional |
| Copy | copy_number | Optional |
| Book_Summary | book_summary | Optional |
| Contents | contents | Optional |
| Keywords | keywords | Optional |
| Publication_Datte | publication_date | Handles typo in column name |
| serial | serial | Used as unique identifier |
| shelf | shelf | Shelf location |

## How to Import

### Step 1: Access Admin Panel
1. Navigate to `http://127.0.0.1:8000/admin/`
2. Login with your admin credentials
3. Go to **Books** section
4. Click on **Books**

### Step 2: Import Data
1. Click the **Import** button at the top of the Books list
2. Choose your Excel file (`Real_ife_sample.xlsx`)
3. Select **xlsx** as the file format
4. Click **Submit**

### Step 3: Review Import
1. The system will show a preview of the data to be imported
2. Review any errors or warnings
3. If everything looks correct, click **Confirm import**

## Data Validation

### Automatic Handling
- **Missing Titles**: Automatically set to "Unknown Title"
- **Missing Authors**: Automatically set to "Unknown Author"
- **Serial Numbers**: Converted to strings for consistency
- **Shelf Locations**: Converted to strings for consistency
- **Publication Date Typo**: Automatically handles "Publication_Datte" column name

### Duplicate Handling
- Books are identified by their **serial** number
- If a book with the same serial already exists, it will be updated
- Use `skip_unchanged = True` to avoid updating unchanged records

## Supported File Formats

- **Excel (.xlsx)** - Primary format
- **Excel (.xls)** - Legacy format
- **CSV (.csv)** - Comma-separated values
- **TSV (.tsv)** - Tab-separated values

## Error Handling

### Common Issues and Solutions

1. **Missing Required Fields**
   - Solution: Ensure Title and Author columns exist
   - System will use defaults for missing values

2. **Invalid Data Types**
   - Solution: Check that numeric fields (Pages, Copy) contain numbers
   - Empty cells are handled automatically

3. **Date Format Issues**
   - Solution: Ensure dates are in a recognizable format (YYYY-MM-DD, MM/DD/YYYY, etc.)
   - Empty date fields are allowed

4. **Large File Size**
   - Solution: Split large files into smaller chunks (recommended: 1000 books per file)
   - Import in batches for better performance

## Best Practices

### Before Import
1. **Backup Database**: Always backup your database before large imports
2. **Test with Sample**: Test with a small subset of data first
3. **Clean Data**: Remove any completely empty rows
4. **Check Encoding**: Ensure file is saved with UTF-8 encoding for special characters

### During Import
1. **Monitor Progress**: Watch for any error messages
2. **Review Preview**: Carefully check the import preview
3. **Check Mappings**: Verify column mappings are correct

### After Import
1. **Verify Data**: Check a few imported books manually
2. **Test Search**: Ensure imported books are searchable
3. **Check Availability**: Verify book availability status

## Advanced Features

### Custom Field Mapping
If your Excel file has different column names, you can modify the mapping in the admin interface or contact your system administrator.

### Bulk Updates
The import system can update existing books if they have the same serial number. This is useful for:
- Updating book conditions
- Adding missing information
- Correcting errors

### Export Functionality
You can also export your current book data to Excel format for backup or sharing:
1. Go to Books admin page
2. Select books to export
3. Choose "Export selected books" action
4. Select Excel format

## Troubleshooting

### Import Fails Completely
1. Check file format is supported
2. Ensure file is not corrupted
3. Verify you have admin permissions
4. Check server logs for detailed errors

### Partial Import Success
1. Review error messages for specific rows
2. Fix data issues in Excel file
3. Re-import only the failed records

### Performance Issues
1. Reduce file size (split into smaller files)
2. Remove unnecessary columns
3. Import during off-peak hours

## Contact Support

If you encounter issues not covered in this guide:
1. Check the system logs
2. Contact your system administrator
3. Provide sample data and error messages

## File Structure Example

Your `Real_ife_sample.xlsx` file structure is fully supported. The system will automatically:
- Map all 30 columns to appropriate database fields
- Handle the "Publication_Datte" typo
- Process all 16 books (or thousands in your full file)
- Maintain data integrity and relationships

**Note**: The system is designed to handle files with thousands of books efficiently. Your real-life data structure is fully compatible with this import system.