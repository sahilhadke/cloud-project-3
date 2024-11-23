import os
import cv2
import json
import boto3
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import warnings
import shutil

warnings.filterwarnings('ignore')
torch.set_grad_enabled(False)

s3_client = boto3.client('s3', region_name='us-east-1')

os.environ['TORCH_HOME'] = '/tmp'
device = torch.device('cpu')
torch.set_num_threads(1)

mtcnn = MTCNN(
    image_size=240,
    margin=0,
    min_face_size=20,
    thresholds=[0.5, 0.6, 0.6],
    device=device,
    post_process=True
)
resnet = InceptionResnetV1(pretrained='vggface2', device=device).eval()

def handler(event, context):
    try:
        os.makedirs('/tmp/models', exist_ok=True)
        os.makedirs('/tmp/checkpoints', exist_ok=True)

        bucket_name = event['bucket_name']
        image_file_name = event['image_file_name']
        input_path = f"/tmp/{image_file_name}"

        # Download image and model data from S3
        s3_client.download_file(bucket_name, image_file_name, input_path)
        s3_client.download_file("1229679960-model", "data.pt", "/tmp/data.pt")

        # Process image
        img = cv2.imread(input_path, cv2.IMREAD_COLOR)
        if img is None:
            raise Exception(f"Failed to read image: {image_file_name}")

        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        face, prob = mtcnn(img_pil, return_prob=True)
        if face is None:
            raise Exception("No face detected")

        # Recognize face
        saved_data = torch.load('/tmp/data.pt', map_location='cpu')
        emb = resnet(face.unsqueeze(0)).detach()
        dist_list = [torch.dist(emb, emb_db).item() for emb_db in saved_data[0]]
        idx_min = dist_list.index(min(dist_list))
        result = saved_data[1][idx_min]

        # Save result to file and upload to S3
        output_file = os.path.splitext(image_file_name)[0] + '.txt'
        output_path = f"/tmp/{output_file}"
        with open(output_path, 'w') as f:
            f.write(result)
        s3_client.upload_file(output_path, "1229679960-output", output_file)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Face recognition completed',
                'result': result,
                'output_file': output_file
            })
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
    finally:
        try:
            for filename in os.listdir('/tmp'):
                file_path = os.path.join('/tmp', filename)
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")

