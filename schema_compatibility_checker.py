#!/usr/bin/env python3
"""
Schema Compatibility Checker
Handles differences between R&D and production database schemas
"""

import asyncio
import asyncpg
import psycopg2
import logging
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class SchemaCompatibilityChecker:
    """Ensure R&D and production schema compatibility"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def check_schema_compatibility(self, rd_config: Dict, prod_config: Dict = None) -> Dict:
        """Compare R&D and production schemas"""
        
        compatibility_report = {
            'compatible': True,
            'issues': [],
            'warnings': [],
            'migration_needed': False,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get R&D schema
            rd_schema = await self.get_postgres_schema(rd_config)
            
            # If no prod config provided, just analyze R&D schema
            if not prod_config:
                self.logger.info("No production config provided, analyzing R&D schema only")
                compatibility_report['rd_schema'] = rd_schema
                
                # Check for common issues
                if 'metadata_columns' in rd_schema:
                    for table, columns in rd_schema['metadata_columns'].items():
                        for col_info in columns:
                            if col_info['data_type'] == 'json':
                                compatibility_report['warnings'].append(
                                    f"Table '{table}' uses 'json' type for column '{col_info['column_name']}'. "
                                    f"Consider using 'jsonb' for better performance and compatibility."
                                )
                
                return compatibility_report
            
            # Get production schema
            prod_schema = await self.get_postgres_schema(prod_config)
            
            # Compare schemas
            schema_diff = self.compare_schemas(rd_schema, prod_schema)
            
            if schema_diff['critical_differences']:
                compatibility_report['compatible'] = False
                compatibility_report['issues'].extend(schema_diff['critical_differences'])
                compatibility_report['migration_needed'] = True
            
            if schema_diff['minor_differences']:
                compatibility_report['warnings'].extend(schema_diff['minor_differences'])
            
            # Check pgvector extension compatibility
            pgvector_compat = await self.check_pgvector_compatibility(rd_config, prod_config)
            if not pgvector_compat['compatible']:
                compatibility_report['compatible'] = False
                compatibility_report['issues'].extend(pgvector_compat['issues'])
            
            # Add migration scripts if needed
            if compatibility_report['migration_needed']:
                compatibility_report['migration_script'] = await self.generate_migration_script(schema_diff)
                compatibility_report['rollback_script'] = self.create_rollback_script(compatibility_report['migration_script'])
            
        except Exception as e:
            compatibility_report['compatible'] = False
            compatibility_report['issues'].append(f"Error checking compatibility: {str(e)}")
            
        return compatibility_report
    
    async def get_postgres_schema(self, config: Dict) -> Dict:
        """Get PostgreSQL schema information"""
        
        schema_info = {
            'tables': {},
            'metadata_columns': {},
            'extensions': [],
            'version': None
        }
        
        try:
            # Connect to database
            conn = await asyncpg.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 5432),
                user=config.get('user'),
                password=config.get('password'),
                database=config.get('database', config.get('dbname'))
            )
            
            # Get PostgreSQL version
            version = await conn.fetchval("SELECT version()")
            schema_info['version'] = version
            
            # Get installed extensions
            extensions = await conn.fetch(
                "SELECT extname, extversion FROM pg_extension"
            )
            schema_info['extensions'] = [
                {'name': ext['extname'], 'version': ext['extversion']} 
                for ext in extensions
            ]
            
            # Get tables with metadata columns
            metadata_query = """
                SELECT 
                    table_name,
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND (column_name LIKE '%metadata%' OR data_type IN ('json', 'jsonb'))
                ORDER BY table_name, ordinal_position
            """
            
            metadata_columns = await conn.fetch(metadata_query)
            
            for col in metadata_columns:
                table_name = col['table_name']
                if table_name not in schema_info['metadata_columns']:
                    schema_info['metadata_columns'][table_name] = []
                
                schema_info['metadata_columns'][table_name].append({
                    'column_name': col['column_name'],
                    'data_type': col['data_type'],
                    'is_nullable': col['is_nullable'],
                    'column_default': col['column_default']
                })
            
            # Get all tables
            tables = await conn.fetch(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """
            )
            
            for table in tables:
                table_name = table['table_name']
                
                # Get column information
                columns = await conn.fetch(
                    """
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = $1
                    ORDER BY ordinal_position
                    """,
                    table_name
                )
                
                schema_info['tables'][table_name] = [
                    {
                        'name': col['column_name'],
                        'type': col['data_type'],
                        'nullable': col['is_nullable'] == 'YES'
                    }
                    for col in columns
                ]
            
            await conn.close()
            
        except Exception as e:
            self.logger.error(f"Error getting schema: {e}")
            raise
            
        return schema_info
    
    def compare_schemas(self, rd_schema: Dict, prod_schema: Dict) -> Dict:
        """Compare two schemas and identify differences"""
        
        differences = {
            'critical_differences': [],
            'minor_differences': [],
            'metadata_type_mismatch': False
        }
        
        # Check metadata column type mismatches
        for table, rd_columns in rd_schema.get('metadata_columns', {}).items():
            prod_columns = prod_schema.get('metadata_columns', {}).get(table, [])
            
            for rd_col in rd_columns:
                col_name = rd_col['column_name']
                rd_type = rd_col['data_type']
                
                # Find matching column in production
                prod_col = next((c for c in prod_columns if c['column_name'] == col_name), None)
                
                if prod_col:
                    prod_type = prod_col['data_type']
                    
                    # Check for json vs jsonb mismatch
                    if (rd_type == 'json' and prod_type == 'jsonb') or \
                       (rd_type == 'jsonb' and prod_type == 'json'):
                        differences['critical_differences'].append({
                            'type': 'metadata_type_mismatch',
                            'table': table,
                            'column': col_name,
                            'rd_type': rd_type,
                            'prod_type': prod_type,
                            'description': f"Type mismatch in {table}.{col_name}: R&D uses {rd_type}, production uses {prod_type}"
                        })
                        differences['metadata_type_mismatch'] = True
                
                else:
                    differences['minor_differences'].append({
                        'type': 'missing_column',
                        'table': table,
                        'column': col_name,
                        'description': f"Column {table}.{col_name} exists in R&D but not in production"
                    })
        
        # Check for missing tables
        rd_tables = set(rd_schema.get('tables', {}).keys())
        prod_tables = set(prod_schema.get('tables', {}).keys())
        
        missing_in_prod = rd_tables - prod_tables
        missing_in_rd = prod_tables - rd_tables
        
        for table in missing_in_prod:
            differences['critical_differences'].append({
                'type': 'missing_table',
                'table': table,
                'description': f"Table {table} exists in R&D but not in production"
            })
        
        for table in missing_in_rd:
            differences['minor_differences'].append({
                'type': 'extra_table',
                'table': table,
                'description': f"Table {table} exists in production but not in R&D"
            })
        
        return differences
    
    async def check_pgvector_compatibility(self, rd_config: Dict, prod_config: Dict) -> Dict:
        """Check pgvector extension compatibility"""
        
        compatibility = {
            'compatible': True,
            'issues': []
        }
        
        try:
            # Check R&D pgvector
            rd_conn = await asyncpg.connect(
                host=rd_config.get('host', 'localhost'),
                port=rd_config.get('port', 5432),
                user=rd_config.get('user'),
                password=rd_config.get('password'),
                database=rd_config.get('database', rd_config.get('dbname'))
            )
            
            rd_pgvector = await rd_conn.fetchval(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            )
            
            await rd_conn.close()
            
            if not rd_pgvector:
                compatibility['compatible'] = False
                compatibility['issues'].append("pgvector extension not installed in R&D environment")
                return compatibility
            
            # Check production pgvector
            prod_conn = await asyncpg.connect(
                host=prod_config.get('host'),
                port=prod_config.get('port', 5432),
                user=prod_config.get('user'),
                password=prod_config.get('password'),
                database=prod_config.get('database', prod_config.get('dbname'))
            )
            
            prod_pgvector = await prod_conn.fetchval(
                "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
            )
            
            await prod_conn.close()
            
            if not prod_pgvector:
                compatibility['compatible'] = False
                compatibility['issues'].append("pgvector extension not installed in production environment")
            elif rd_pgvector != prod_pgvector:
                compatibility['issues'].append(
                    f"pgvector version mismatch: R&D has {rd_pgvector}, production has {prod_pgvector}"
                )
            
        except Exception as e:
            compatibility['compatible'] = False
            compatibility['issues'].append(f"Error checking pgvector compatibility: {str(e)}")
        
        return compatibility
    
    async def generate_migration_script(self, schema_diff: Dict) -> str:
        """Generate safe migration script for production"""
        
        migration_sql = [
            "-- Auto-generated migration script",
            f"-- Generated at: {datetime.now().isoformat()}",
            "-- Run in transaction for safety",
            "BEGIN;",
            "",
            "-- Schema compatibility fixes"
        ]
        
        # Handle json vs jsonb conversion
        if schema_diff.get('metadata_type_mismatch'):
            migration_sql.append("\n-- Convert metadata columns to jsonb for compatibility")
            
            for diff in schema_diff['critical_differences']:
                if diff['type'] == 'metadata_type_mismatch' and diff['rd_type'] == 'json':
                    table = diff['table']
                    column = diff['column']
                    migration_sql.extend([
                        f"\n-- Convert {table}.{column} from json to jsonb",
                        f"ALTER TABLE {table} ALTER COLUMN {column} TYPE jsonb USING {column}::jsonb;",
                    ])
        
        # Add new columns if needed
        for diff in schema_diff.get('minor_differences', []):
            if diff['type'] == 'missing_column':
                migration_sql.append(
                    f"\n-- Note: Column {diff['table']}.{diff['column']} exists in R&D but not in production"
                )
        
        migration_sql.extend([
            "",
            "-- Verify migration success",
            "SELECT 'Migration completed successfully' as status;",
            "",
            "COMMIT;"
        ])
        
        return "\n".join(migration_sql)
    
    def create_rollback_script(self, migration_script: str) -> str:
        """Create rollback script for safe deployment"""
        
        rollback_sql = [
            "-- Auto-generated rollback script",
            f"-- Generated at: {datetime.now().isoformat()}",
            "BEGIN;",
            "",
            "-- Rollback schema changes",
            "-- NOTE: This may cause data loss - use with caution",
            ""
        ]
        
        # Add specific rollback commands based on migration
        if "ALTER COLUMN" in migration_script and "TYPE jsonb" in migration_script:
            # Extract table and column names from migration script
            import re
            pattern = r"ALTER TABLE (\w+) ALTER COLUMN (\w+) TYPE jsonb"
            matches = re.findall(pattern, migration_script)
            
            for table, column in matches:
                rollback_sql.extend([
                    f"-- Rollback {table}.{column} from jsonb to json",
                    f"ALTER TABLE {table} ALTER COLUMN {column} TYPE json USING {column}::json;",
                    ""
                ])
        
        rollback_sql.extend([
            "SELECT 'Rollback completed' as status;",
            "COMMIT;"
        ])
        
        return "\n".join(rollback_sql)
    
    async def fix_metadata_compatibility(self, config: Dict) -> Dict:
        """Apply compatibility fixes to handle json/jsonb differences"""
        
        result = {
            'success': False,
            'changes_made': [],
            'errors': []
        }
        
        try:
            conn = await asyncpg.connect(
                host=config.get('host', 'localhost'),
                port=config.get('port', 5432),
                user=config.get('user'),
                password=config.get('password'),
                database=config.get('database', config.get('dbname'))
            )
            
            # Check current metadata columns
            metadata_columns = await conn.fetch(
                """
                SELECT table_name, column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND column_name LIKE '%metadata%'
                    AND data_type IN ('json', 'jsonb')
                """
            )
            
            for col in metadata_columns:
                if col['data_type'] == 'json':
                    # Convert to jsonb for better compatibility
                    try:
                        await conn.execute(
                            f"ALTER TABLE {col['table_name']} "
                            f"ALTER COLUMN {col['column_name']} "
                            f"TYPE jsonb USING {col['column_name']}::jsonb"
                        )
                        result['changes_made'].append(
                            f"Converted {col['table_name']}.{col['column_name']} from json to jsonb"
                        )
                    except Exception as e:
                        result['errors'].append(
                            f"Failed to convert {col['table_name']}.{col['column_name']}: {str(e)}"
                        )
            
            await conn.close()
            
            result['success'] = len(result['errors']) == 0
            
        except Exception as e:
            result['errors'].append(f"Connection error: {str(e)}")
        
        return result


async def main():
    """Test schema compatibility checker"""
    import asyncio
    from dotenv import load_dotenv
    
    load_dotenv()
    
    checker = SchemaCompatibilityChecker()
    
    # R&D configuration
    rd_config = {
        'host': os.getenv('PG_HOST', 'localhost'),
        'port': int(os.getenv('PG_PORT', 5432)),
        'user': os.getenv('PG_USER'),
        'password': os.getenv('PG_PASSWORD'),
        'database': os.getenv('PG_DBNAME', 'mem0_test')
    }
    
    # Check R&D schema
    print("🔍 Checking R&D schema compatibility...")
    report = await checker.check_schema_compatibility(rd_config)
    
    print(f"\n📊 Compatibility Report:")
    print(f"   Compatible: {report['compatible']}")
    print(f"   Issues: {len(report['issues'])}")
    print(f"   Warnings: {len(report['warnings'])}")
    
    if report['issues']:
        print("\n❌ Critical Issues:")
        for issue in report['issues']:
            print(f"   - {issue}")
    
    if report['warnings']:
        print("\n⚠️ Warnings:")
        for warning in report['warnings']:
            print(f"   - {warning}")
    
    if report.get('migration_script'):
        print("\n📝 Migration Script:")
        print(report['migration_script'])
        
        # Save migration script
        with open('schema_migration.sql', 'w') as f:
            f.write(report['migration_script'])
        print("\n💾 Migration script saved to: schema_migration.sql")
        
        # Save rollback script
        with open('schema_rollback.sql', 'w') as f:
            f.write(report['rollback_script'])
        print("💾 Rollback script saved to: schema_rollback.sql")


if __name__ == "__main__":
    asyncio.run(main()) 