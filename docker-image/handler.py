import boto3
import os
import subprocess
from urllib.parse import unquote_plus

# Initialize S3 client
s3_client = boto3.client('s3')

def extract_frames(input_file_path, output_folder, frame_rate="1/10", total_frames=10):
    """
    Extract frames from a video file using ffmpeg.
    """
    os.makedirs(output_folder, exist_ok=True)
    output_pattern = os.path.join(output_folder, "output_%02d.jpg")

    # Run ffmpeg command to extract frames
    subprocess.run([
        "ffmpeg", "-ss", "0", "-r", "1", "-i", input_file_path,
        "-vf", f"fps={frame_rate}", "-start_number", "0",
        "-vframes", str(total_frames), output_pattern, "-y"
    ])

def handler(event, context):
    # Parse S3 event to get the bucket and object key
    for record in event['Records']:
        source_bucket = record['s3']['bucket']['name']
        source_key = unquote_plus(record['s3']['object']['key'])
        
        # Define destination bucket and folder based on source key
        destination_bucket = "1229679960-stage-1"  # Update with your destination bucket name
        output_folder_name = os.path.splitext(os.path.basename(source_key))[0]
        
        # Download video file from S3
        input_file_path = f"/tmp/{os.path.basename(source_key)}"
        s3_client.download_file(source_bucket, source_key, input_file_path)
        
        # Extract frames
        output_folder = f"/tmp/{output_folder_name}"
        extract_frames(input_file_path, output_folder)
        
        # Upload frames back to destination S3 bucket
        for frame_file in os.listdir(output_folder):
            frame_file_path = os.path.join(output_folder, frame_file)
            s3_key = f"{output_folder_name}/{frame_file}"
            
            # Upload frame to S3
            s3_client.upload_file(frame_file_path, destination_bucket, s3_key)
        
        # Clean up temporary files
        os.remove(input_file_path)
        for frame_file in os.listdir(output_folder):
            os.remove(os.path.join(output_folder, frame_file))
        os.rmdir(output_folder)

    return {
        'statusCode': 200,
        'body': 'Frames extracted and uploaded successfully!'
    }
