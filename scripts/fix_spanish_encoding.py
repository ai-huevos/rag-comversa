#!/usr/bin/env python3
"""
Fix Spanish Character Encoding in Database

This script fixes corrupted Spanish characters (accents, ñ, etc.) in all text fields
across all tables in the database.

Common issues:
- "Ingeniería" appears as "Ingenier\u00eda"
- "gestión" appears as "gesti\u00f3n"
- "planificación" appears as "planificaci\u00f3n"
"""
import sqlite3
import sys
from pathlib import Path
import unicodedata

PROJECT_ROOT = Path(__file__).parent.parent


def normalize_spanish_text(text):
    """
    Normalize Spanish text by properly handling Unicode characters
    
    Args:
        text: String that may contain corrupted Spanish characters
        
    Returns:
        Properly encoded Spanish text
    """
    if not text or not isinstance(text, str):
        return text
    
    # First, try to decode if it's been double-encoded
    try:
        # If text contains \uXXXX sequences, decode them
        if '\\u' in text:
            # Use unicode_escape to decode \uXXXX sequences
            text = text.encode('utf-8').decode('unicode_escape')
    except Exception:
        pass
    
    # Normalize to NFC form (composed characters)
    # This ensures "é" is one character, not "e" + combining accent
    text = unicodedata.normalize('NFC', text)
    
    return text


def get_text_columns(cursor, table_name):
    """Get all TEXT columns from a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Return column names that are TEXT type
    text_columns = [col[1] for col in columns if col[2] == 'TEXT']
    return text_columns


def fix_table_encoding(cursor, table_name):
    """Fix encoding issues in all TEXT columns of a table"""
    print(f"\n🔧 Fixing {table_name}...")
    
    # Get all TEXT columns
    text_columns = get_text_columns(cursor, table_name)
    
    if not text_columns:
        print(f"  ⊘ No TEXT columns found")
        return 0
    
    print(f"  📝 TEXT columns: {', '.join(text_columns)}")
    
    # Get all rows
    cursor.execute(f"SELECT id, {', '.join(text_columns)} FROM {table_name}")
    rows = cursor.fetchall()
    
    if not rows:
        print(f"  ⊘ No rows to fix")
        return 0
    
    fixed_count = 0
    
    for row in rows:
        row_id = row[0]
        updates = []
        values = []
        
        # Check each text column
        for i, col_name in enumerate(text_columns):
            original_value = row[i + 1]  # +1 because row[0] is id
            
            if original_value:
                normalized_value = normalize_spanish_text(original_value)
                
                # If value changed, add to update
                if normalized_value != original_value:
                    updates.append(f"{col_name} = ?")
                    values.append(normalized_value)
        
        # If any columns need updating, update the row
        if updates:
            values.append(row_id)  # For WHERE clause
            update_sql = f"UPDATE {table_name} SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(update_sql, values)
            fixed_count += 1
    
    if fixed_count > 0:
        print(f"  ✓ Fixed {fixed_count} rows")
    else:
        print(f"  ✓ No encoding issues found")
    
    return fixed_count


def fix_database_encoding(db_path):
    """Fix encoding issues in entire database"""
    print("=" * 60)
    print("SPANISH CHARACTER ENCODING FIX")
    print("=" * 60)
    print(f"Database: {db_path}")
    
    if not db_path.exists():
        print(f"\n❌ Database not found: {db_path}")
        return False
    
    # Connect to database
    print("\n📂 Connecting to database...")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"📊 Found {len(tables)} tables")
    
    total_fixed = 0
    
    # Fix each table
    for table in tables:
        try:
            fixed = fix_table_encoding(cursor, table)
            total_fixed += fixed
        except Exception as e:
            print(f"  ❌ Error fixing {table}: {e}")
    
    # Commit changes
    print(f"\n💾 Committing changes...")
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ ENCODING FIX COMPLETE")
    print("=" * 60)
    print(f"Total rows fixed: {total_fixed}")
    
    if total_fixed > 0:
        print("\n✨ Spanish characters should now display correctly!")
        print("   Examples: Ingeniería, gestión, planificación, coordinación")
    else:
        print("\n✓ No encoding issues found - database is clean!")
    
    return True


def show_sample_data(db_path, table_name="pain_points", limit=5):
    """Show sample data to verify the fix"""
    print("\n" + "=" * 60)
    print(f"SAMPLE DATA FROM {table_name}")
    print("=" * 60)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT description FROM {table_name} LIMIT {limit}")
        rows = cursor.fetchall()
        
        for i, row in enumerate(rows, 1):
            print(f"{i}. {row[0]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()


def main():
    """Main entry point"""
    
    # Default to full_intelligence.db
    db_path = PROJECT_ROOT / "data" / "full_intelligence.db"
    
    # Allow command line argument
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    
    print("\n🇪🇸 Spanish Character Encoding Fix Tool")
    print(f"Target: {db_path.name}\n")
    
    # Fix the database
    success = fix_database_encoding(db_path)
    
    if success:
        # Show sample data
        show_sample_data(db_path)
        
        print("\n💡 TIP: To fix other databases, run:")
        print(f"   python3 scripts/fix_spanish_encoding.py data/intelligence.db")
        print(f"   python3 scripts/fix_spanish_encoding.py data/pilot_intelligence.db")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
