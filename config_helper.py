"""
Universal Sheet Config Helper
Provides dynamic header/field mapping for entire system.
No more hardcoded header names!
"""
import json
import os


class ConfigHelper:
    """
    Central config reader for sheet_config.json
    Makes entire system dynamic and config-driven
    """
    
    def __init__(self, config_path="sheet_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.mapping = self.config.get("column_mapping", {})
        self.field_defaults = self.config.get("field_defaults", {})
    
    def _load_config(self):
        """Load sheet_config.json"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_header_for_field(self, field_path):
        """
        Given a field path like 'ai_resume' or 'id', 
        return the header name user set in config
        
        Example:
            field_path = 'ai_resume'
            returns 'Resume' or 'Resu_' or whatever user named it
        """
        for header, field in self.mapping.items():
            if field == field_path:
                return header
        return None
    
    def get_field_for_header(self, header_name):
        """
        Given a header name, return the field path it maps to
        
        Example:
            header_name = 'Resume'
            returns 'ai_resume'
        """
        return self.mapping.get(header_name)
    
    def get_all_headers(self):
        """Get list of all headers in order defined in config"""
        return list(self.mapping.keys())
    
    def get_all_fields(self):
        """Get list of all field paths"""
        return list(self.mapping.values())
    
    def get_default_value(self, field_path):
        """
        Get default value for empty fields from field_defaults
        Falls back to "Not Mentioned" if not specified
        """
        return self.field_defaults.get(field_path, "Not Mentioned")
    
    def detect_changes(self, sheet_headers):
        """
        Compare actual sheet headers with config
        Returns: (added, removed) - headers that don't match
        """
        config_headers = set(self.get_all_headers())
        sheet_header_set = set(sheet_headers)
        
        added = sheet_header_set - config_headers
        removed = config_headers - sheet_header_set
        
        return list(added), list(removed)
    
    def notify_header_changes(self, sheet_headers):
        """
        Print console notification if headers in sheet 
        don't match config
        
        Returns True if changes detected
        """
        added, removed = self.detect_changes(sheet_headers)
        
        if added or removed:
            print("\n" + "="*50)
            print("⚠️  HEADER CHANGES DETECTED")
            print("="*50)
            
            if removed:
                print(f"❌ Missing in Sheet: {', '.join(removed)}")
                print("   (These are in config but not in actual sheet)")
            
            if added:
                print(f"➕ New in Sheet: {', '.join(added)}")
                print("   (These are in sheet but not in config)")
            
            print("\n💡 Tip: Update sheet_config.json to match your sheet")
            print("="*50 + "\n")
            return True
        
        return False
    
    def get_spreadsheet_id(self):
        """Get spreadsheet ID from config"""
        return self.config.get("spreadsheet_id")
    
    def get_spreadsheet_name(self):
        """Get spreadsheet name from config"""
        return self.config.get("spreadsheet_name", "LinkedIn Jobs")
    
    def get_sheet_name(self):
        """Get sheet name from config"""
        return self.config.get("sheet_name", "Sheet1")


# Convenience function for quick usage
def get_config():
    """Get a ConfigHelper instance"""
    return ConfigHelper()


if __name__ == "__main__":
    # Test the helper
    config = ConfigHelper()
    print("📋 All Headers:", config.get_all_headers())
    print("\n🔍 Testing field lookup:")
    print(f"  'id' field → Header: {config.get_header_for_field('id')}")
    print(f"  'ai_resume' field → Header: {config.get_header_for_field('ai_resume')}")
    print(f"  'ai_cover_letter' field → Header: {config.get_header_for_field('ai_cover_letter')}")
