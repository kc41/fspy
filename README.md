# FSPY

Client and server for remote file system activity monitoring.

## Environment

* Python: 3.6
* OS: tested on Windows and MacOS.

## Installation
```bash
pip install -U git+https://github.com/kc41/fspy.git
```

## Usage

### Server
```bash
python -m fspy.collector --db_path $SQLITE_DB_PATH
```
This command will start HTTP server at `0.0.0.0:10455` 
 and create SQLite DB file `SQLITE_DB_PATH` (if not exists).
 
For addition keys see `python -m fspy.collector -h`

#### Endpoints

##### /flat_report
Endpoint for reports. Query parameters:
* date_start: `2018-09-02T23:00:00`. Required.
* date_end: `2018-09-02T23:15:00`. Required.
* source: `pc_1`. Optional.

If timezone not provided - treated as local server time.

Response example:
```json
{
  "entries": [
    {
      "source_name": "pc_1",
      "source_ip": "192.168.158.20",
      "file_path": "/var/log/app/1.log",
      "operation": "CREATE",
      "size_before": null,
      "size_after": 256,
      "operation_time": "2018-09-02T16:13:48.070242+00:00"
    },
    {
      "source_name": "pc_1",
      "source_ip": "192.168.158.20",
      "file_path": "/var/log/app/1.log",
      "operation": "UPDATE",
      "size_before": 256,
      "size_after": 512,
      "operation_time": "2018-09-02T16:14:17.730938+00:00"
    }
  ]
}
```


##### /ws?source_name=$SOME_NAME
Endpoint for WS-connections from agents.
 Source name must be provided in query parameter `source_name`

### Client
```bash
python -m fspy.agent --source_name $SOME_NAME --server_host $FSPY_SERVER_IP --target $DIR_TO_WATCH
```

* `$SOME_NAME` - name of changes source (used in reports)
* `$FSPY_SERVER_IP` - IP address or hostname of FSPY server
* `$DIR_TO_WATCH` - directory to watch

For addition keys see `python -m fspy.agent -h`
