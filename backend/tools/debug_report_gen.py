import sys
import os
# Add backend to path
sys.path.append(os.getcwd())

from backend.app.services.reports import generate_sla_pdf

# Dummy Data
mock_data = [
    {"name": "Tower A - Radio 1", "ip": "192.168.1.10", "availability_percent": 100.0, "avg_latency_ms": 2.5},
    {"name": "Tower B - AP 5", "ip": "192.168.1.11", "availability_percent": 98.5, "avg_latency_ms": 15.2},
    {"name": "Client X", "ip": "192.168.1.12", "availability_percent": 94.0, "avg_latency_ms": 45.0},
]
# Add 50 more items to force pagination
for i in range(50):
    mock_data.append({
        "name": f"Device {i}", 
        "ip": f"10.0.0.{i}", 
        "availability_percent": 99.9, 
        "avg_latency_ms": 1.0
    })

mock_stats = {
    "global_uptime": 99.15,
    "global_latency": 5.4,
    "critical_devices_count": 1,
    "conclusion": "Test Conclusion string.",
    "pie_data": [10, 5, 1, 1],
    "line_data": [("01/01", 99.0), ("02/01", 99.5), ("03/01", 98.0)]
}

period = "01/01/2026 ate 07/01/2026"

print("Generating SLA PDF...")
try:
    buf = generate_sla_pdf(mock_data, period, mock_stats)
    print(f"Success! Buffer size: {len(buf.getvalue())} bytes")
    # Write to verify
    with open("test_sla.pdf", "wb") as f:
        f.write(buf.getvalue())
    print("Saved test_sla.pdf")
except Exception as e:
    print("CRASHED:")
    import traceback
    traceback.print_exc()

print("-" * 30)

from backend.app.services.reports import generate_incidents_pdf
print("Generating Incidents PDF...")
mock_inc_stats = {
    "total_devices": 100,
    "total_drops": 5,
    "total_recoveries": 5,
    "top_problematic": [{"name": "BadDev", "ip": "1.1.1.1", "drops": 10}],
    "conclusion": "Incidents Conclusion.",
    "daily_evolution": [("01/01", 2), ("02/01", 3)]
}
try:
    buf2 = generate_incidents_pdf([], period, mock_inc_stats)
    print(f"Success! Buffer size: {len(buf2.getvalue())} bytes")
except Exception as e:
    print("CRASHED INCIDENTS:")
    import traceback
    traceback.print_exc()
