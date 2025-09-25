import os
import json
import logging
from typing import Dict, Any, List
from database import db
import discord

class MigrationManager:
    def __init__(self, bot):
        self.bot = bot
        self.json_files_to_migrate = [
            'mainbank.json',
            'leveling.json', 
            'user_mood_data.json',
            'server_mood_data.json',
            'server_settings.json',
            'announcement_settings.json',
            'warnings.json',
            'qotd.json',
            'prefixes.json',
            'mention_prefs.json',
            'mental_health_config.json',
            'mood_dates.json',
            'log_channels.json',
            'level_up_channels.json',
            'leveling_enabled.json',
            'ignored_channels.json'
        ]
    
    async def run_migration(self) -> Dict[str, Any]:
        """Run the complete migration process"""
        logging.info("Starting migration process...")
        
        migration_report = {
            "status": "started",
            "database_connected": False,
            "migration_needed": False,
            "migration_completed": False,
            "files_found": [],
            "files_missing": [],
            "migration_results": {},
            "files_deleted": [],
            "deletion_errors": [],
            "error": None
        }
        
        try:
            # Connect to database
            if await db.connect():
                migration_report["database_connected"] = True
                logging.info("Database connection established")
            else:
                migration_report["error"] = "Failed to connect to database"
                return migration_report
            
            # Create tables
            await db.create_tables()
            logging.info("Database tables created/verified")
            
            # Check if migration already completed
            if await db.is_migration_completed():
                migration_report["status"] = "already_completed"
                logging.info("Migration already completed, skipping...")
                return migration_report
            
            migration_report["migration_needed"] = True
            
            # Check which JSON files exist
            for filename in self.json_files_to_migrate:
                if os.path.exists(filename):
                    migration_report["files_found"].append(filename)
                else:
                    migration_report["files_missing"].append(filename)
            
            if not migration_report["files_found"]:
                migration_report["status"] = "no_files_to_migrate"
                logging.info("No JSON files found to migrate")
                await db.mark_migration_completed()
                return migration_report
            
            # Perform migration
            logging.info(f"Migrating {len(migration_report['files_found'])} JSON files to database...")
            migration_results = await db.migrate_json_data()
            migration_report["migration_results"] = migration_results
            
            if migration_results["errors"]:
                logging.warning(f"Migration completed with {len(migration_results['errors'])} errors")
            else:
                logging.info("Migration completed successfully")
            
            # Mark migration as completed
            await db.mark_migration_completed()
            migration_report["migration_completed"] = True
            
            # Delete JSON files after successful migration
            await self._delete_migrated_files(migration_report)
            
            migration_report["status"] = "completed"
            
        except Exception as e:
            logging.error(f"Migration failed: {str(e)}")
            migration_report["error"] = str(e)
            migration_report["status"] = "failed"
        
        return migration_report
    
    async def _delete_migrated_files(self, migration_report: Dict[str, Any]):
        """Delete JSON files after successful migration"""
        for filename in migration_report["files_found"]:
            try:
                # Create backup directory if it doesn't exist
                if not os.path.exists("json_backups"):
                    os.makedirs("json_backups")
                
                # Move file to backup instead of deleting (safer approach)
                backup_path = f"json_backups/{filename}.backup"
                os.rename(filename, backup_path)
                migration_report["files_deleted"].append(f"{filename} -> {backup_path}")
                logging.info(f"Moved {filename} to {backup_path}")
                
            except Exception as e:
                error_msg = f"Failed to backup {filename}: {str(e)}"
                migration_report["deletion_errors"].append(error_msg)
                logging.error(error_msg)
    
    def create_migration_embed(self, migration_report: Dict[str, Any]) -> discord.Embed:
        """Create a Discord embed with migration results"""
        
        if migration_report["status"] == "already_completed":
            embed = discord.Embed(
                title="🔄 Database Migration",
                description="Migration has already been completed previously.",
                color=0x00ff00
            )
            return embed
        
        if migration_report["status"] == "failed":
            embed = discord.Embed(
                title="❌ Database Migration Failed",
                description=f"Migration failed with error: {migration_report.get('error', 'Unknown error')}",
                color=0xff0000
            )
            return embed
        
        if migration_report["status"] == "no_files_to_migrate":
            embed = discord.Embed(
                title="🔄 Database Migration",
                description="No JSON files found to migrate. Database is ready to use.",
                color=0x00ff00
            )
            return embed
        
        # Successful migration
        embed = discord.Embed(
            title="✅ Database Migration Completed",
            description="Successfully migrated JSON data to MySQL database",
            color=0x00ff00
        )
        
        # Add database connection info
        embed.add_field(
            name="🔗 Database Connection",
            value="✅ Connected to MySQL database" if migration_report["database_connected"] else "❌ Failed to connect",
            inline=False
        )
        
        # Add migration statistics
        results = migration_report.get("migration_results", {})
        if results:
            success_list = results.get("success", [])
            error_list = results.get("errors", [])
            total_records = results.get("total_records", 0)
            
            embed.add_field(
                name="📊 Migration Statistics",
                value=f"**Total Records Migrated:** {total_records}\n**Successful:** {len(success_list)}\n**Errors:** {len(error_list)}",
                inline=True
            )
            
            if success_list:
                success_text = "\n".join(success_list[:10])  # Limit to first 10 to avoid embed limits
                if len(success_list) > 10:
                    success_text += f"\n... and {len(success_list) - 10} more"
                embed.add_field(
                    name="✅ Successfully Migrated",
                    value=f"```\n{success_text}\n```",
                    inline=False
                )
            
            if error_list:
                error_text = "\n".join(error_list[:5])  # Limit errors to avoid embed size limits
                if len(error_list) > 5:
                    error_text += f"\n... and {len(error_list) - 5} more errors"
                embed.add_field(
                    name="❌ Errors",
                    value=f"```\n{error_text}\n```",
                    inline=False
                )
        
        # Add file backup info
        files_deleted = migration_report.get("files_deleted", [])
        if files_deleted:
            backup_text = "\n".join(files_deleted[:8])  # Limit to avoid embed limits
            if len(files_deleted) > 8:
                backup_text += f"\n... and {len(files_deleted) - 8} more"
            embed.add_field(
                name="🗂️ Files Backed Up",
                value=f"```\n{backup_text}\n```",
                inline=False
            )
        
        deletion_errors = migration_report.get("deletion_errors", [])
        if deletion_errors:
            embed.add_field(
                name="⚠️ Backup Warnings",
                value=f"```\n{deletion_errors[0]}\n```",
                inline=False
            )
        
        embed.add_field(
            name="🎯 Next Steps",
            value="• JSON files have been backed up to `json_backups/`\n• Bot is now using MySQL database\n• Old JSON files are safely preserved",
            inline=False
        )
        
        embed.set_footer(text="Migration completed successfully! Bot is now database-powered.")
        
        return embed