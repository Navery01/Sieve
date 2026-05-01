# main.py
import logging, argparse, sys, os, asyncio

from .agents.detection_agent import DetectionAgent
from .crawlers.structured_crawler import StructuredCrawler
from .connectors.rdbms.postgres_connector import PostgresConnector
from .crawlers.crawler_scopes.structured_scope import StructuredScope

from pprint import pprint

def parse_arguments():
    parser = argparse.ArgumentParser(description="Client Agent for Task Execution")
    parser.add_argument("-d", "--directory", type=str, default="/", help="Path to file directory to scan for PII data")
    parser.add_argument("-s", "--server", type=str, default="localhost", help="Name of server instance to connect to")
    parser.add_argument("-p", "--port", type=str, default="5432", help="Port number to connect to")
    parser.add_argument("-u", "--username", type=str, default="username", help="Username for database connection")
    parser.add_argument("-w", "--password", type=str, default="password", help="Password for database connection")
    
    return parser.parse_args()

async def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Agent is starting...")
    logging.getLogger("presidio-analyzer").setLevel(logging.ERROR)
    logging.getLogger("presidio-anonymizer").setLevel(logging.ERROR)
    args = parse_arguments()
    
    # Initialize the agent
    agent = DetectionAgent()
    crawler = StructuredCrawler()
    connector = PostgresConnector()

    server = args.server
    port = args.port

    await connector.connect(host=server, user=args.username, password=args.password, port=port, ssl_verify=False)
    scope = StructuredScope()
    await crawler.initialize(connector, scope)
    await crawler.crawl()

    pprint(crawler.structure_info)

if __name__ == "__main__":    
    asyncio.run(main())


