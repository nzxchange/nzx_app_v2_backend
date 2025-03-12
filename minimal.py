# The most minimal possible lambda handler for Vercel
def handler(event, context):
    """Minimal handler that just returns a success response"""
    return {
        "statusCode": 200,
        "body": '{"message": "Minimal handler is working"}',
        "headers": {"Content-Type": "application/json"}
    } 