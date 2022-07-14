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

## demo
- bgpquery
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

