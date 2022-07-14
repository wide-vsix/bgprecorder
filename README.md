# bgp route collector

Create a BGP RIB time series database from MRT format dump files.

## how to deploy
### docker
1. Create docker-compose.yml with reference to docker-compose.sample.yml.
2. Create .env
```
BGPRECORDER_DB_HOST=postgres
BGPRECORDER_DB_PORT=5432
BGPRECORDER_DB_NAME=bgprecorder
BGPRECORDER_DB_USER=postgres
BGPRECORDER_DB_PASSWORD=PASSWORD

```
3. run
```
docker-compose up -d
```


### native install
TBD

## CLI tool

### bgprecord

```
$ bgprecorder  -h 
usage: bgprecorder [-h] [-H DB_HOST] [-p DB_PORT] [-u DB_USER] [-w DB_PASSWORD] [-d DB_NAME] [-c COMPRESS] [-i DURATION] [-f MRT_DUMP_FILES]

bgprecord dump BGP MRT rib to DB

optional arguments:
  -h, --help            show this help message and exit
  -H DB_HOST, --db_host DB_HOST
                        db host. default: localhost or $BGPRECORDER_DB_HOST
  -p DB_PORT, --db_port DB_PORT
                        db port. default: 5432 or $BGPRECORDER_DB_PORT
  -u DB_USER, --db_user DB_USER
                        db user. default: postgres or $BGPRECORDER_DB_USER
  -w DB_PASSWORD, --db_password DB_PASSWORD
                        db password. default: None or $BGPRECORDER_DB_PASSWORD
  -d DB_NAME, --db_name DB_NAME
                        db name. default: bgprecorder or $BGPRECORDER_DB_RECORDER
  -c COMPRESS, --compress COMPRESS
                        compress MRT dump after import. default: False
  -i DURATION, --duration DURATION
                        interval of recording (sec.) default: 3600 or $BGPRECORDER_DURATION
  -f MRT_DUMP_FILES, --mrt_dump_files MRT_DUMP_FILES
                        target MRT dumpfile match rule. default: ./mrt/*.dump or $BGPRECORDER_DURATION
```


```
$ bash misc/env.sh
$ bgprecord 
```

### bgpquery
```
$ bgpquery  -h 
usage: bgpquery [-h] -a ADDRESS [-t DATETIME] [-H DB_HOST] [-p DB_PORT] [-u DB_USER] [-w DB_PASSWORD] [-d DB_NAME]

bgpquery: get BGP rib json from bgprecorder db

optional arguments:
  -h, --help            show this help message and exit
  -a ADDRESS, --address ADDRESS
                        target address
  -t DATETIME, --datetime DATETIME
                        target datetime. example: "200601021504"
  -H DB_HOST, --db_host DB_HOST
                        db host. default: localhost or $BGPRECORDER_DB_HOST
  -p DB_PORT, --db_port DB_PORT
                        db port. default: 5432 or $BGPRECORDER_DB_PORT
  -u DB_USER, --db_user DB_USER
                        db user. default: postgres or $BGPRECORDER_DB_USER
  -w DB_PASSWORD, --db_password DB_PASSWORD
                        db user. default: None or $BGPRECORDER_DB_PASSWORD
  -d DB_NAME, --db_name DB_NAME
                        db user. default: bgprecorder or $BGPRECORDER_DB_RECORDER
```

```
$ bash misc/env.sh
$ bgpquery -a 3ffe::114  -d 202207131800  | jq
{
  "id": 13735,
  "time": "2022-07-13T17:00:32",
  "path_id": 3204,
  "type_name": "TABLE_DUMP2_AP",
  "sequence": null,
  "from_ip": "2001:200:e00:300:dad::4",
  "from_as": 0,
  "originated": null,
  "origin": "IGP",
  "aspath": "400 300",
  "nlri_type": null,
  "nlri": "3ffe::/32",
  "nexthop": "2001:db8::ace",
  "community": "4690:64500",
  "large_community": null
}
{
  "id": 13736,
  "time": "2022-07-13T17:00:32",
  "path_id": 4634,
  "type_name": "TABLE_DUMP2_AP",
  "sequence": null,
  "from_ip": "2001:200:e00:300:dad::5",
  "from_as": 0,
  "originated": null,
  "origin": "IGP",
  "aspath": "100 200 300",
  "nlri_type": null,
  "nlri": "3ffe::/32",
  "nexthop": "2001:db8::beaf",
  "community": "4690:64501",
  "large_community": null
}
```

