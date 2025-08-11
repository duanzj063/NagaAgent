#!/usr/bin/env python3
"""
Neo4j连接测试脚本
用于测试与远程Neo4j数据库的连接
"""

import sys
import os
from neo4j import GraphDatabase
import argparse

def test_neo4j_connection(uri, user, password):
    """
    测试Neo4j连接
    """
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 测试连接
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) AS count LIMIT 1")
            count = result.single()["count"]
            print(f"✅ Neo4j连接成功!")
            print(f"   数据库URI: {uri}")
            print(f"   用户名: {user}")
            print(f"   检测到节点数量: {count}")
            
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Neo4j连接失败: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='测试Neo4j连接')
    parser.add_argument('--uri', help='Neo4j URI', default='neo4j://36.111.150.30:7687')
    parser.add_argument('--user', help='用户名', default='neo4j')
    parser.add_argument('--password', help='密码', default='X9!m#K2@dL6qR8')
    
    args = parser.parse_args()
    
    print("正在测试Neo4j连接...")
    print(f"目标地址: {args.uri}")
    
    success = test_neo4j_connection(args.uri, args.user, args.password)
    
    if success:
        print("\n🎉 Neo4j连接测试通过!")
        return 0
    else:
        print("\n💥 Neo4j连接测试失败!")
        return 1

if __name__ == "__main__":
    sys.exit(main())