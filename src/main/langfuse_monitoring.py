import os
from datetime import datetime, timedelta
from langfuse import Langfuse

# Langfuse Configuration
LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_HOST = os.getenv("LANGFUSE_HOST")

# Alert Configuration
TRACE_COUNT_THRESHOLD = int(os.environ.get("TRACE_COUNT_THRESHOLD", "2"))
TIME_WINDOW_HOURS = int(os.environ.get("TIME_WINDOW_HOURS", "12"))

def get_all_observation_levels():
    """
    Query Langfuse API and print levels for all observations across all pages
    """
    print("Initializing Langfuse client...")
    # Initialize Langfuse client
    langfuse = Langfuse(
        secret_key=LANGFUSE_SECRET_KEY,
        public_key=LANGFUSE_PUBLIC_KEY,
        host=LANGFUSE_HOST
    )
    
    # Calculate the time range for filtering
    to_start_time = datetime.utcnow()
    from_start_time = to_start_time - timedelta(hours=TIME_WINDOW_HOURS)
    
    print(f"Fetching observations from {from_start_time} to {to_start_time}")
    
    # For storing all observations
    all_observations = []
    
    # For pagination
    current_page = 1
    page_size = 50  # Adjust based on your API's page size limits
    total_pages = 1  # Initial value, will be updated after first fetch
    
    # Loop through all pages
    while current_page <= total_pages:
        print(f"Fetching page {current_page}...")
        
        # Fetch observations for the current page
        observations = langfuse.fetch_observations(
            from_start_time=from_start_time,
            to_start_time=to_start_time,
            page=current_page,
            limit=page_size
        )
        
        # Add current page observations to our collection
        all_observations.extend(observations.data)
        
        # Update total pages if this is the first page
        if current_page == 1:
            # Calculate total pages based on total items and page size
            total_items = observations.meta.total_items
            total_pages = (total_items + page_size - 1) // page_size 
            print(f"Total observations: {total_items}, Total pages: {total_pages}")
        
        # Move to the next page
        current_page += 1
        
        # Break if no more data (safeguard)
        if not observations.data:
            break
    
    # Create a dictionary to count occurrences of each level
    level_counts = {}
    
    # Process all observations
    for observation in all_observations:
        obs_dict = observation.dict()
        level = obs_dict.get('level', 'None')
        
        # Count occurrences of each level
        if level in level_counts:
            level_counts[level] += 1
        else:
            level_counts[level] = 1
            
    # Print summary of level counts
    print("\nLevel distribution:")
    for level, count in level_counts.items():
        print(f"{level}: {count} observations")
    
    # Count error observations specifically
    error_count = level_counts.get('ERROR', 0)
    print(f"\nTotal error observations: {error_count}")
    
    return error_count, level_counts

def main():
    """
    Main function to check trace count and send alert if needed
    """
    print("Starting Langfuse error monitoring...")
    try:
        trace_count, level_counts = get_all_observation_levels()
        print(f"Current trace count: {trace_count}, Threshold: {TRACE_COUNT_THRESHOLD}")
        
        if trace_count >= TRACE_COUNT_THRESHOLD:
            print("Trace count exceeded threshold, sending alert...")
            # The GitHub Action will handle sending the email alert
            # based on this output message
        else:
            print("Trace count is below threshold, no action needed.")
    
    except Exception as e:
        print(f"Error in trace monitoring: {str(e)}")
        # Exit with non-zero status to indicate failure
        exit(1)

if __name__ == "__main__":
    main()