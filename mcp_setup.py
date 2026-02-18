import os
from dotenv import load_dotenv
from logger_config import setup_logger

logger = setup_logger("MCP_Setup")
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "Agent"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "admin123"),
}

def get_postgres_connection_string() -> str:
    """Generate PostgreSQL connection string for MCP server"""
    return (
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )


def get_mcp_server_config():
    try:
        env = os.environ.copy()
        env.update({
            "PGHOSTADDR": DB_CONFIG["host"],
            "PGPORT": DB_CONFIG["port"],
            "PGDATABASE": DB_CONFIG["database"],
            "PGUSER": DB_CONFIG["user"],
            "PGPASSWORD": DB_CONFIG["password"],
        })
        logger.info("MCP Server config generated.")
        return {
            "command": "postgres-mcp-server",
            "args": [f"postgresql://{DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"],
            "env": env,
            "transport": "stdio",
        }
    except Exception as e:
        logger.error(f"Failed to build MCP server config: {str(e)}")
        return None
    

def validate_config():
    """Validate that all required configuration is present"""
    try:
        required_fields = ["host", "port", "database", "user", "password"]
        missing = [f for f in required_fields if not DB_CONFIG.get(f)]

        if missing:
            raise ValueError(f"Missing configuration fields: {', '.join(missing)}")
        
        logger.info("Configuration validated successfully")
        return True
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise

if __name__ == "__main__":

    validate_config()
    print("MCP Server Config loaded successfully")