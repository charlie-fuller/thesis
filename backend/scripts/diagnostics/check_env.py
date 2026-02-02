import os

from dotenv import load_dotenv

load_dotenv()

required_vars = {
    "Core Services": [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
    ],
    "AI Services": ["ANTHROPIC_API_KEY", "VOYAGE_API_KEY", "GOOGLE_GENERATIVE_AI_API_KEY"],
    "Configuration": ["FRONTEND_URL", "DEFAULT_CLIENT_ID", "CLIENT_NAME", "ASSISTANT_NAME"],
}

print("Environment Configuration Status:\n")
for category, vars in required_vars.items():
    print(f"📋 {category}:")
    for var in vars:
        value = os.getenv(var)
        if value and not value.startswith("your-"):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - NOT SET")
    print()
