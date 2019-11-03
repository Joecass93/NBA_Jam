from pymongo import MongoClient


def main():
    return MongoClient("mongodb://admin:Moneyteam2019@cluster0-shard-00-00-vwlhe.mongodb.net:27017,cluster0-shard-00-01-vwlhe.mongodb.net:27017,cluster0-shard-00-02-vwlhe.mongodb.net:27017/admin?ssl=true&replicaSet=Cluster0-shard-0&authSource=admin&retryWrites=true&w=majority")
