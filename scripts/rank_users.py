import os
import psycopg2
from psycopg2 import sql
from tabulate import tabulate
import datetime

def get_db_connection():
    """Establishes a connection to the database."""
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="jeanmemorytypefasho",
            host="db.masapxpxcwvsjpuymbmd.supabase.co",
            port="5432"
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        print("Please ensure the database credentials are correct and the database is accessible.")
        exit(1)

def get_table_schema(conn, table_name):
    """Retrieves the schema of a given table."""
    print(f"\nAnalyzing schema for table: '{table_name}'")
    try:
        with conn.cursor() as cur:
            cur.execute(sql.SQL("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s;
            """), (table_name,))
            schema = cur.fetchall()
            if schema:
                print(tabulate(schema, headers=["Column Name", "Data Type"], tablefmt="grid"))
            else:
                print(f"Could not retrieve schema for table '{table_name}'. It might not exist or is not accessible.")
    except psycopg2.Error as e:
        print(f"Error retrieving schema for table '{table_name}': {e}")


def rank_users_by_engagement(conn):
    """Ranks power users by engagement and saves it to a Markdown file."""
    print("\nRanking power users by engagement (number of memories created)...")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    u.id as user_id,
                    u.email,
                    u.name,
                    COUNT(m.id) as memory_count
                FROM
                    users u
                LEFT JOIN
                    memories m ON u.id = m.user_id
                GROUP BY
                    u.id, u.email, u.name
                ORDER BY
                    memory_count DESC;
            """)
            user_engagement = cur.fetchall()

            if user_engagement:
                headers = ["User ID", "Email", "Name", "Memory Count"]
                
                # Console output
                print("User Engagement Rankings:")
                print(tabulate(user_engagement, headers=headers, tablefmt="grid"))
                
                # Markdown file output
                md_content = f"# User Engagement Rankings\n\n_Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
                md_content += tabulate(user_engagement, headers=headers, tablefmt="github")
                
                output_filename = "scripts/user_rankings.md"
                with open(output_filename, "w") as f:
                    f.write(md_content)
                print(f"\nSuccessfully saved user rankings to '{output_filename}'")
                
            else:
                print("No user engagement data found.")
    except psycopg2.Error as e:
        print(f"Error ranking users: {e}")

def rank_users_by_momentum(conn):
    """Ranks users by momentum and saves it to a Markdown file."""
    print("\nRanking users by momentum...")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    u.id as user_id,
                    u.email,
                    u.name,
                    u.created_at as user_created_at,
                    array_agg(m.created_at ORDER BY m.created_at) as memory_timestamps
                FROM
                    users u
                JOIN
                    memories m ON u.id = m.user_id
                WHERE
                    u.created_at IS NOT NULL
                GROUP BY
                    u.id, u.email, u.name, u.created_at
                HAVING
                    count(m.id) > 0;
            """)
            user_data = cur.fetchall()

            momentum_scores = []
            today = datetime.datetime.now(datetime.timezone.utc)

            for user in user_data:
                user_id, email, name, user_created_at, memory_timestamps = user
                
                if not user_created_at or not memory_timestamps:
                    continue

                if user_created_at.tzinfo is None:
                    user_created_at = user_created_at.replace(tzinfo=datetime.timezone.utc)

                days_since_creation = (today - user_created_at).days
                if days_since_creation <= 0:
                    days_since_creation = 1

                memory_count = len(memory_timestamps)
                engagement_rate = memory_count / days_since_creation

                consistency = 0.5
                if memory_count > 1:
                    time_diffs = [(memory_timestamps[i] - memory_timestamps[i-1]).total_seconds() for i in range(1, memory_count)]
                    mean_diff = sum(time_diffs) / len(time_diffs)
                    if mean_diff > 0:
                        std_dev = (sum([(d - mean_diff) ** 2 for d in time_diffs]) / len(time_diffs)) ** 0.5
                        consistency = 1 / (std_dev / mean_diff + 1)

                last_memory_date = max(memory_timestamps)
                if last_memory_date.tzinfo is None:
                    last_memory_date = last_memory_date.replace(tzinfo=datetime.timezone.utc)
                days_since_last_memory = (today - last_memory_date).days
                recency_bonus = 1 / (days_since_last_memory + 1)

                increasing_rate_bonus = 1.0
                if memory_count > 5:
                    first_half = memory_timestamps[:memory_count//2]
                    second_half = memory_timestamps[memory_count//2:]
                    if len(first_half) > 1 and len(second_half) > 1:
                        first_half_interval = (first_half[-1] - first_half[0]).total_seconds() / (len(first_half) -1)
                        second_half_interval = (second_half[-1] - second_half[0]).total_seconds() / (len(second_half) -1)
                        if second_half_interval > 0 and first_half_interval > second_half_interval:
                            increasing_rate_bonus = 1.5

                momentum_score = engagement_rate * (1 + consistency + recency_bonus) * increasing_rate_bonus
                
                momentum_scores.append({
                    "User ID": user_id,
                    "Email": email,
                    "Name": name,
                    "Momentum Score": round(momentum_score, 4),
                    "Memory Count": memory_count,
                    "Days Since Creation": days_since_creation
                })

            momentum_scores = sorted(momentum_scores, key=lambda x: x["Momentum Score"], reverse=True)

            if momentum_scores:
                headers = {
                    "User ID": "User ID", "Email": "Email", "Name": "Name", 
                    "Momentum Score": "Momentum Score", "Memory Count": "Memory Count", 
                    "Days Since Creation": "Days Since Creation"
                }
                
                print("\nUser Momentum Rankings:")
                print(tabulate(momentum_scores, headers=headers, tablefmt="grid"))
                
                md_content = f"# User Momentum Rankings\n\n_Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_\n\n"
                md_content += tabulate(momentum_scores, headers="keys", tablefmt="github")
                
                output_filename = "scripts/user_momentum_rankings.md"
                with open(output_filename, "w") as f:
                    f.write(md_content)
                print(f"\nSuccessfully saved user momentum rankings to '{output_filename}'")
                
            else:
                print("No user momentum data found.")

    except psycopg2.Error as e:
        print(f"Error ranking users by momentum: {e}")

def main():
    """Main function to run the analysis."""
    print("Starting database analysis for Jean Memory...")
    
    conn = get_db_connection()
    
    if conn:
        print("Successfully connected to the database.")
        
        # Analyze table schemas
        get_table_schema(conn, "users")
        get_table_schema(conn, "memories")
        
        # Rank users by engagement
        rank_users_by_engagement(conn)
        
        # Rank users by momentum
        rank_users_by_momentum(conn)
        
        # Close the connection
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    print("To run this script, you may need to install the required Python libraries:")
    print("pip install psycopg2-binary tabulate")
    main() 