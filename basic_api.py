from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Basic API is working"}

# Vercel serverless handler (without Mangum)
def handler(event, context):
    path = event.get('path', '/')
    
    # If root path, return our simple response
    if path == '/':
        return {
            "statusCode": 200,
            "body": '{"message": "Basic API is working"}',
            "headers": {"Content-Type": "application/json"}
        }
    else:
        return {
            "statusCode": 404,
            "body": '{"error": "Not found"}',
            "headers": {"Content-Type": "application/json"}
        } 