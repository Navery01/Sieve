# main.py
import logging, argparse, sys, os

def parse_arguments():
    parser = argparse.ArgumentParser(description="Client Agent for Task Execution")
    parser.add_argument("-d", type=str, default="/", help="Path to file directory to scan for PII data")
    parser.add_argument("--directory", type=str, default="/", help="Path to file directory to scan for PII data")
    parser.add_argument("-s", type=str, default="localhost", help="Name of server instance to connect to")
    parser.add_argument("--server", type=str, default="localhost", help="Name of server instance to connect to")
    parser.add_argument("-p", type=str, default="5432", help="Port number to connect to")
    parser.add_argument("--port", type=str, default="5432", help="Port number to connect to")
    
    
    return parser.parse_args()

def main():
    logging.basicConfig(level=logging.INFO)
    logging.info("Agent is starting...")

    # Initialize the agent