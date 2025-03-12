import os
from dotenv import load_dotenv

# Load .env.development if it exists
if os.path.exists(".env.development"):
    load_dotenv(".env.development")
    print("Loaded .env.development")
else:
    load_dotenv()
    print("Loaded .env")

# Print all environment variables and their values
print("\nEnvironment Variables:")
for name, value in os.environ.items():
    # Skip sensitive values
    if any(sensitive in name.lower() for sensitive in ["key", "secret", "password", "token"]):
        value = "***REDACTED***"
    print(f"{name}: {value}")

# Try to manually parse CORS_ORIGINS
cors_origins = os.environ.get("CORS_ORIGINS")
print(f"\nCORS_ORIGINS raw value: {cors_origins!r}")

if cors_origins == "*":
    print("Parsed as wildcard: ['*']")
elif "," in cors_origins:
    parsed = [item.strip() for item in cors_origins.split(",")]
    print(f"Parsed as comma-separated list: {parsed}")
else:
    print(f"Using as single value: [{cors_origins}]")

print("\nTest complete") 