import re

# Simulate what we read from .env
raw = 'postgresql://postgres:Ragul_0209@localhost:5432/"SAFEGAS IoT"'
print("RAW:", repr(raw))

# Step 1: After reading from .env, the value is the above string (no outer strip needed)
# The issue: the regex /\"([^\"]+)\"$ should match /"SAFEGAS IoT"

fixed = re.sub(r'/"([^"]+)"$', lambda m: '/' + m.group(1).replace(' ', '%20'), raw)
print("AFTER REGEX:", repr(fixed))
print("DISPLAY:", fixed)
