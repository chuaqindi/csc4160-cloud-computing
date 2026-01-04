import pickle
import json

# Load the model
filename = 'iris_model.sav'
model = pickle.load(open(filename, 'rb'))

def predict(features):
    return model.predict(features).tolist()

def lambda_handler(event, context):
    # TODO: Implement your own lambda_handler logic here
    # You will need to extract the 'values' from the event and call the predict function.
    
    try:
        # 1. Extract the body (could be a JSON string or dict)
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)

        # 2. Extract "values"
        values = body.get("values")
        if not values:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Missing 'values' in request body"})
            }

        # 3. Call predict
        predictions = predict(values)

        # 4. Return JSON response in Lambda proxy format
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"predictions": predictions})
        }

    except Exception as e:
        # Catch errors and return as 500
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }

    
