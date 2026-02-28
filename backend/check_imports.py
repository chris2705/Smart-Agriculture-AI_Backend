try:
    import fastapi
    print("fastapi ok")
    import uvicorn
    print("uvicorn ok")
    import sqlalchemy
    print("sqlalchemy ok")
    import jose
    print("jose ok")
    import passlib
    print("passlib ok")
    from google.cloud import storage
    print("google.cloud.storage ok")
    import google.generativeai
    print("google.generativeai ok")
except Exception as e:
    print(f"FAILED: {e}")
