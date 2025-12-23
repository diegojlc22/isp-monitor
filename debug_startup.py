import sys
print("🔍 Testing Imports...")

try:
    print("1. Importing main...")
    from backend.app import main
    print("✅ Main imported.")
    
    print("2. Importing snmp_monitor...")
    from backend.app.services import snmp_monitor
    print("✅ SNMP Monitor imported.")
    
    print("3. Importing maintenance...")
    from backend.app.services import maintenance
    print("✅ Maintenance imported.")

except Exception as e:
    print(f"❌ Import Failed: {e}")
    import traceback
    traceback.print_exc()

print("🏁 Test Complete.")
