from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["ZTproj30"]

print("Number of documents in 'voices':", db.voices.count_documents({}))
