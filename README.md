### Grading Script
```
python3 grader_script_p1.py --access_key <ACCESS_KEY> --secret_key <SECRET_KEY> --input_bucket 1229679960-input --output_bucket 1229679960-stage-1 --lambda_name video-splitting
```

### Workload Generator
```
python3 workload_generator.py \
 --access_key <ACCESS_KEY> \
 --secret_key <SECRET_KEY> \
 --input_bucket 1229679960-input \
 --output_bucket 1229679960-stage-1 \
 --testcase_folder /Users/sahilhadke/Desktop/PROJECTS/cloud-project-3/dataset/test_case_1/
```