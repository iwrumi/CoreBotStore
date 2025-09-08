#!/usr/bin/env python3
"""
Migration script to move data from JSON files to PostgreSQL database
"""
import os
from data_manager import DataManager as JSONDataManager
from advanced_data_manager import AdvancedDataManager

def main():
    print("🚀 Starting migration from JSON to PostgreSQL...")
    
    try:
        # Initialize both data managers
        json_manager = JSONDataManager()
        db_manager = AdvancedDataManager()
        
        print("✅ Database connection established")
        
        # Migrate data
        print("📦 Migrating data...")
        db_manager.migrate_from_json(json_manager)
        
        print("🎉 Migration completed successfully!")
        print("\n📊 Summary:")
        
        # Show migration results
        products = db_manager.get_products()
        orders = db_manager.get_orders()
        users = db_manager.get_users()
        
        print(f"   Products migrated: {len(products)}")
        print(f"   Orders migrated: {len(orders)}")
        print(f"   Users migrated: {len(users)}")
        
        print("\n🎯 Your store is now powered by PostgreSQL with advanced features!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == '__main__':
    main()