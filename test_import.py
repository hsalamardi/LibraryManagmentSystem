#!/usr/bin/env python
"""
Test script for importing Real_ife_sample.xlsx
This script tests the import functionality without using the admin interface.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.append(str(project_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nta_library.settings')
django.setup()

from books.admin import BookResource
from tablib import Dataset
import pandas as pd

def test_import():
    """Test importing the Real_ife_sample.xlsx file"""
    print("Testing Real Life Excel Import...")
    
    # Read the Excel file
    try:
        df = pd.read_excel('Real_ife_sample.xlsx')
        print(f"✓ Successfully read Excel file with {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        return False
    
    # Convert to tablib Dataset
    try:
        dataset = Dataset()
        dataset.headers = df.columns.tolist()
        
        for _, row in df.iterrows():
            dataset.append(row.tolist())
        
        print(f"✓ Successfully converted to dataset with {len(dataset)} rows")
    except Exception as e:
        print(f"✗ Error converting to dataset: {e}")
        return False
    
    # Test the import resource
    try:
        book_resource = BookResource()
        result = book_resource.import_data(dataset, dry_run=True)
        
        print(f"✓ Import test completed:")
        print(f"  - Total rows: {result.total_rows}")
        print(f"  - New records: {len(result.rows)}")
        print(f"  - Invalid rows: {len(result.invalid_rows)}")
        
        if result.has_errors():
            print("\n⚠ Errors found:")
            for i, error in enumerate(result.row_errors()):
                if i < 5:  # Show only first 5 errors
                    print(f"  Row {error[0]}: {error[1]}")
                elif i == 5:
                    print(f"  ... and {len(result.row_errors()) - 5} more errors")
                    break
        else:
            print("\n✓ No errors found - import would be successful!")
            
        # Show validation details
        if result.invalid_rows:
            print("\n📋 Validation Issues:")
            for i, invalid_row in enumerate(result.invalid_rows[:3]):
                print(f"  Row {invalid_row.number}: {invalid_row.error}")
                if i == 2 and len(result.invalid_rows) > 3:
                    print(f"  ... and {len(result.invalid_rows) - 3} more validation issues")
                    break
            
        return True
        
    except Exception as e:
        print(f"✗ Error during import test: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_sample_data():
    """Show sample of the data that would be imported"""
    try:
        df = pd.read_excel('Real_ife_sample.xlsx')
        print("\n📊 Sample Data Preview:")
        print("=" * 50)
        
        # Show first few rows with key columns
        key_columns = ['serial', 'Title', 'Author', 'ISBN', 'Publisher']
        available_columns = [col for col in key_columns if col in df.columns]
        
        if available_columns:
            sample_df = df[available_columns].head(3)
            print(sample_df.to_string(index=False))
        else:
            print("Key columns not found, showing first 3 rows of all data:")
            print(df.head(3).to_string())
            
    except Exception as e:
        print(f"Error showing sample data: {e}")

if __name__ == "__main__":
    print("Real Life Excel Import Test")
    print("=" * 40)
    
    # Show sample data first
    show_sample_data()
    
    # Test the import
    print("\n🧪 Testing Import Process:")
    print("=" * 40)
    success = test_import()
    
    if success:
        print("\n🎉 Import test completed successfully!")
        print("\n📝 Next Steps:")
        print("1. Go to http://127.0.0.1:8000/admin/")
        print("2. Navigate to Books > Books")
        print("3. Click 'Import' button")
        print("4. Upload your Real_ife_sample.xlsx file")
        print("5. Review and confirm the import")
    else:
        print("\n❌ Import test failed. Please check the errors above.")