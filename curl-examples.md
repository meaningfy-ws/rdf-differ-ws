## Set of `curl` commands to test the `api`


### get diffs
```bash
curl -X 'GET' \
    'http://localhost:4030/diffs' \
    -H 'accept: application/json'
```

### get specific diff
change `dataset_id` to the desired dataset name.
```bash
curl -X 'GET' \
    'http://localhost:4030/diffs/<dataset_id>' \
    -H 'accept: application/json'
```

### create diff
change `dataset_id`, `dataset_uri`, `new_version_id` and `old_version_id` to the desired data.
```bash
curl -X 'POST' \
    `'http://localhost:4030/diffs' \
    -H 'accept: */*' \
    -H 'Content-Type: multipart/form-data' \
    -F 'dataset_description=' \
    -F 'dataset_id=<dataset_id>' \
    -F 'dataset_uri=<dataset_uri>' \
    -F 'new_version_file_content=@tests/test_data/original/data_theme/new-data-theme-skos-ap-act.rdf;type=application/rdf+xml' \
    -F 'new_version_id=new' \
    -F 'old_version_file_content=@tests/test_data/original/data_theme/old-data-theme-skos-ap-act.rdf;type=application/rdf+xml' \
    -F 'old_version_id=old'
```

### check task status
change `task_id` to the desired task id.
```bash
curl -X 'GET' \
  'http://localhost:4030/tasks/<task_id>' \
  -H 'accept: application/json'
```


###revoke running for a task
change `task_id` to the desired task id.
```bash
curl -X 'DELETE' \
  'http://localhost:4030/tasks/<task_id>' \
  -H 'accept: application/json'
```

### request building for specific AP report type
change `application_profile`, `dataset_id` and `template_type`  to the desired data.
```bash
curl -X 'POST' \
  'http://localhost:4030/diffs/report' \
  -H 'accept: */*' \
  -H 'Content-Type: application/json' \
  -d '{
  "application_profile": "skos-ap",
  "dataset_id": "<dataset_id>",
  "template_type": "json"
}'
```

### get report for specific AP report type
change `application_profile`, `dataset_id` and `template_type`  to the desired data.

```bash
curl -X 'GET' \
  'http://localhost:4030/diffs/report?dataset_id=<dataset_id>&application_profile=skos-ap&template_type=json'
```