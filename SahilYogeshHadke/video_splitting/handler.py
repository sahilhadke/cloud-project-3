import json
import os
import subprocess
import boto3
from urllib.parse import unquote_plus

# Initialize AWS clients
s3 = boto3.client('s3', region_name='us-east-1')
lambda_client = boto3.client('lambda', region_name='us-east-1')

def handler(event, context):
    """
    Process video and extract frame, then trigger the face recognition Lambda function.
    """
    try:
        print(event)

        # S3 bucket names
        input_bucket = "1229679960-input"
        stage_1_bucket = "1229679960-stage-1"

        # Extract information from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        encoded_key = event['Records'][0]['s3']['object']['key']
        decoded_key = unquote_plus(encoded_key, encoding='utf-8')
        video_name = os.path.splitext(os.path.basename(decoded_key))[0]

        video_temp_path = f"/tmp/{decoded_key}"
        output_path = f"/tmp/{video_name}.jpg"

        # Download video from S3
        s3.download_file(bucket, decoded_key, video_temp_path)
        if not os.path.isfile(video_temp_path):
            raise FileNotFoundError("Video file download failed")

        # Extract a single frame from the video
        command = [
            "ffmpeg", '-i', video_temp_path, '-vframes', '1', output_path, '-y'
        ]
        subprocess.run(command, check=True)

        # Upload frame to S3
        frame_key = f"{video_name}.jpg"

        # convert test_0.mp4 to test_00.mp4 (make double digits)
        if len(video_name.split("_")[1]) == 1:
            frame_key = video_name.split("_")[0] + "_0" + video_name.split("_")[1] + ".jpg"
        

        s3.upload_file(output_path, stage_1_bucket, frame_key)
        print(f"Uploaded {frame_key} to S3")

        # Trigger the face recognition Lambda function
        payload = {
            "bucket_name": stage_1_bucket,
            "image_file_name": frame_key
        }
        lambda_client.invoke(
            FunctionName='face-recognition',
            InvocationType='Event',
            Payload=json.dumps(payload)
        )

        return {
            "status": "success",
            "message": "Video processed and face recognition triggered"
        }

    except Exception as e:
        print("Error:", e)
        return {
            "status": "error",
            "message": str(e)
        }

