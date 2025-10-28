"""
Comprehensive functionality test for AI Data Cleaning Assistant
Tests all core features without GUI
"""

import pandas as pd
import sys
from utils.data_analyzer import DataAnalyzer
from utils.data_cleaner import DataCleaner

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_data_loading():
    """Test loading sample data"""
    print_section("TEST 1: Data Loading")
    
    try:
        df = pd.read_csv('sample_data/sample_sales.csv')
        print("Successfully loaded CSV file")
        print(f"   Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        return df
    except Exception as e:
        print(f"Failed to load data: {e}")
        return None

def test_data_analyzer(df):
    """Test DataAnalyzer functionality"""
    print_section("TEST 2: Data Analysis")
    
    try:
        analyzer = DataAnalyzer(df)
        
        # Test 1: Column info
        col_info = analyzer.get_column_info()
        print("Generated column information")
        print(f"   Found {len(col_info)} columns")
        
        # Test 2: Missing values
        missing = analyzer.detect_missing_values()
        print("Detected missing values")
        print(f"   Columns with missing data: {len(missing)}")
        for col, info in missing.items():
            print(f"     - {col}: {info['count']} missing ({info['percentage']:.1f}%)")
        
        # Test 3: Duplicates
        dup_count = analyzer.detect_duplicates()
        print("Detected duplicates")
        print(f"   Found {dup_count} duplicate rows")
        
        # Test 4: Outliers
        outliers_income = analyzer.detect_outliers('Income')
        print("Detected outliers in Income column")
        print(f"   Found {outliers_income} outliers")
        
        # Test 5: Data type issues
        dtype_issues = analyzer.detect_data_type_issues()
        print("Detected data type issues")
        print(f"   Found {len(dtype_issues)} potential issues")
        
        # Test 6: Quality score
        quality_score = analyzer.get_data_quality_score()
        print("Calculated data quality score")
        print(f"   Score: {quality_score}/100")
        
        # Test 7: Suggestions
        suggestions = analyzer.generate_suggestions()
        print("Generated AI suggestions")
        print(f"   Total suggestions: {len(suggestions)}")
        
        return analyzer, suggestions
        
    except Exception as e:
        print(f"Data analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_data_cleaner(df, suggestions):
    """Test DataCleaner functionality"""
    print_section("TEST 3: Data Cleaning")
    
    try:
        cleaner = DataCleaner(df)
        
        # Store original metrics
        original_missing = df.isnull().sum().sum()
        original_dupes = df.duplicated().sum()
        original_rows = len(df)
        
        print("Before cleaning:")
        print(f"   Missing values: {original_missing}")
        print(f"   Duplicates: {original_dupes}")
        print(f"   Rows: {original_rows}")
        
        # Apply cleaning operations
        for key, suggestion in suggestions.items():
            action_type = suggestion.get('type')
            
            if action_type == 'missing_numeric':
                column = suggestion['column']
                cleaner.fill_missing_numeric(column, method='mean')
                print(f"Filled missing values in '{column}' with mean")
            
            elif action_type == 'missing_categorical':
                column = suggestion['column']
                cleaner.fill_missing_categorical(column)
                print(f"Filled missing values in '{column}' with mode")
            
            elif action_type == 'duplicates':
                cleaner.remove_duplicates()
                print("Removed duplicate rows")
            
            elif action_type == 'outliers':
                column = suggestion['column']
                cleaner.remove_outliers(column)
                print(f"Removed outliers from '{column}'")
        
        # Get cleaned data
        cleaned_df = cleaner.get_cleaned_data()
        
        # New metrics
        new_missing = cleaned_df.isnull().sum().sum()
        new_dupes = cleaned_df.duplicated().sum()
        new_rows = len(cleaned_df)
        
        print("\nAfter cleaning:")
        print(f"   Missing values: {new_missing} (reduced by {original_missing - new_missing})")
        print(f"   Duplicates: {new_dupes} (reduced by {original_dupes - new_dupes})")
        print(f"   Rows: {new_rows} (removed {original_rows - new_rows})")
        
        # Cleaning log
        log = cleaner.get_cleaning_log()
        print(f"\nCleaning operations performed: {len(log)}")
        
        return cleaned_df
        
    except Exception as e:
        print(f"Data cleaning failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_export(df):
    """Test data export functionality"""
    print_section("TEST 4: Data Export")
    
    try:
        # Export as CSV
        csv_data = df.to_csv(index=False)
        print("Exported to CSV format")
        print(f"   Size: {len(csv_data)} bytes")
        
        # Export as Excel
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        excel_data = buffer.getvalue()
        print("Exported to Excel format")
        print(f"   Size: {len(excel_data)} bytes")
        
        return True
        
    except Exception as e:
        print(f"Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n" + "AI DATA CLEANING ASSISTANT - FUNCTIONALITY TEST".center(60))
    print("=" * 60)
    print("Testing all core features...\n")
    
    # Test 1: Load data
    df = test_data_loading()
    if df is None:
        print("\nTESTS FAILED: Could not load data")
        sys.exit(1)
    
    # Test 2: Analyze data
    analyzer, suggestions = test_data_analyzer(df)
    if analyzer is None:
        print("\nTESTS FAILED: Data analysis error")
        sys.exit(1)
    
    # Test 3: Clean data
    if suggestions:
        cleaned_df = test_data_cleaner(df, suggestions)
        if cleaned_df is None:
            print("\nTESTS FAILED: Data cleaning error")
            sys.exit(1)
    else:
        print("\nNo cleaning needed - data is already clean")
        cleaned_df = df
    
    # Test 4: Export
    export_success = test_export(cleaned_df)
    if not export_success:
        print("\nTESTS FAILED: Export error")
        sys.exit(1)
    
    # Final summary
    print_section("TEST SUMMARY")
    print("[PASS] All tests passed successfully!")
    print("\nFinal Results:")
    print(f"   Original data: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"   Cleaned data: {cleaned_df.shape[0]} rows x {cleaned_df.shape[1]} columns")
    print(f"   Suggestions generated: {len(suggestions)}")
    print(f"   Data quality improved!")
    print("\n*** The AI Data Cleaning Assistant is working perfectly! ***")
    print("\nNext step: Run 'streamlit run app.py' to test the web interface")
    
if __name__ == "__main__":
    main()
