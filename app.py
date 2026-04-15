from flask import Flask, request, jsonify
from azure.cosmos import CosmosClient, exceptions
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime

# redeploy_3

load_dotenv()

app = Flask(__name__)

connection_string = os.environ.get("COSMOS_CONNECTION_STRING")
client = CosmosClient.from_connection_string(connection_string)

database = client.get_database_client("posts")
container = database.get_container_client("postContainer")


@app.route("/posts", methods=["GET"])
def get_posts():
    posts = list(container.read_all_items())
    return jsonify(posts)


@app.route("/posts/<id>", methods=["GET"])
def get_post(id):
    query = "SELECT * FROM c WHERE c.id = @id"
    parameters = [{"name": "@id", "value": id}]
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))

    if not items:
        return jsonify({"error": "Post not found"}), 404

    return jsonify(items[0])


@app.route("/posts", methods=["POST"])
def create_post():
    data = request.get_json()

    post = {
        "id": str(uuid.uuid4()),
        "title": data.get("title"),
        "content": data.get("content"),
        "author": data.get("author"),
        "timestamp": datetime.utcnow().isoformat()
    }

    container.create_item(body=post)
    return jsonify(post), 201


@app.route("/posts/<id>", methods=["DELETE"])
def delete_post(id):
    query = "SELECT * FROM c WHERE c.id = @id"
    parameters = [{"name": "@id", "value": id}]
    items = list(container.query_items(
        query=query,
        parameters=parameters,
        enable_cross_partition_query=True
    ))

    if not items:
        return jsonify({"error": "Post not found"}), 404

    post = items[0]
    container.delete_item(item=post["id"], partition_key=post["author"])

    return jsonify({"message": "Post deleted"})


if __name__ == "__main__":
    app.run(debug=True)
