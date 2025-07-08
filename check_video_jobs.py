import os
import firebase_admin
from firebase_admin import credentials, db
import json
from datetime import datetime, timedelta
import time

def format_timestamp(timestamp):
    """Convert timestamp to human-readable format."""
    try:
        # Try parsing as Unix timestamp
        if isinstance(timestamp, (int, float)) or (isinstance(timestamp, str) and timestamp.isdigit()):
            dt = datetime.fromtimestamp(float(timestamp))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        # Try parsing as ISO format
        elif isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            return str(timestamp)
    except:
        return str(timestamp)

def get_timestamp_value(timestamp):
    """Convert timestamp to Unix timestamp for comparison."""
    try:
        # Try parsing as Unix timestamp
        if isinstance(timestamp, (int, float)) or (isinstance(timestamp, str) and timestamp.isdigit()):
            return float(timestamp)
        # Try parsing as ISO format
        elif isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.timestamp()
        else:
            return 0
    except:
        return 0

def main():
    # Initialize Firebase Admin SDK
    cred_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    if not cred_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return
        
    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://taajirah-default-rtdb.europe-west1.firebasedatabase.app',
            'databaseAuthVariableOverride': {
                'uid': 'service-account',
                'token': {
                    'email': 'taajirah-agents@taajirah.iam.gserviceaccount.com'
                }
            }
        })
        
        # Get all video jobs
        jobs_ref = db.reference('/video_jobs')
        jobs = jobs_ref.get()
        
        if not jobs:
            print("No video jobs found")
            return
            
        # Convert to list and sort by creation time
        job_list = []
        for job_id, job_data in jobs.items():
            created_at = job_data.get('createdAt', 0)
            created_at_value = get_timestamp_value(created_at)
            job_list.append((job_id, job_data, created_at_value))
            
        # Sort by creation time (newest first)
        job_list.sort(key=lambda x: x[2], reverse=True)
        
        # Get current time
        now = time.time()
        
        print("\n=== Recent Video Jobs (Last 24 Hours) ===")
        print("Current time:", datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S'))
        print("")
        
        recent_jobs = [job for job in job_list if now - job[2] < 24 * 60 * 60]
        
        if not recent_jobs:
            print("No jobs found in the last 24 hours")
            return
            
        # Count jobs by status
        status_counts = {}
        for _, job_data, _ in recent_jobs:
            status = job_data.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
        print("Status Summary:")
        for status, count in sorted(status_counts.items()):
            print(f"- {status}: {count}")
        print("")
            
        for job_id, job_data, created_at in recent_jobs:
            print(f"\nJob ID: {job_id}")
            print("Status:", job_data.get('status', 'unknown'))
            print("Model:", job_data.get('model', 'unknown'))
            print("Created At:", format_timestamp(job_data.get('createdAt')))
            if job_data.get('vertex_job_id'):
                print("Vertex Job ID:", job_data['vertex_job_id'])
            if job_data.get('output_url'):
                print("Video URL:", job_data['output_url'])
            if job_data.get('error'):
                print("Error:", job_data['error'])
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 