from pymongo import MongoClient

def main():
    return MongoClient("mongodb://sfadmin:socialfulcrum19!@sf-test-shard-00-00-3t2nx.mongodb.net:27017,sf-test-shard-00-01-3t2nx.mongodb.net:27017,sf-test-shard-00-02-3t2nx.mongodb.net:27017/test?ssl=true&replicaSet=SF-Test-shard-0&authSource=admin&retryWrites=true")
