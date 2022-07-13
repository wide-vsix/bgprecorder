# bgp route collector

MRT formated bgp rib dump  to psql

```yaml
version: "3"
services:
  cron:
    image: ghcr.io/wide-vsix/simple-cron:latest
    environment:
      TZ: Asia/Tokyo
      CRON_OPTION: "0 3 * * *" # once a day
      CRON_COMMAND: |
        # rsync flom remote
        rsync -tvz -6 vsix@ex-collector:/var/log/gobgp/ribs/*.dump /backup"

        # delete 14 days age files
        find /var/log/gobgp/ribs/ -type f -name "*.dump*" -mtime +14 | xargs -I arg echo Dlete file: arg
        find /var/log/gobgp/ribs/ -type f -name "*.dump*" -mtime +14 | xargs -I arg rm arg
        # compress 7 days ages file
        find /var/log/gobgp/ribs/ -type f -name "*.dump" -mtime +7  | xargs -I arg echo Compress file: arg
        find /var/log/gobgp/ribs/ -type f -name "*.dump" -mtime +7  | xargs -I arg bzip2 arg

    volumes:
      - /var/log/gobgp:/var/log/gobgp
```


## demo
`bgprecorder/client.py` 

```
(bgprecorder-ymYf6BG--py3.8) yas-nyan@analysis:~/bgprecorder$ python3 bgprecorder/client.py  -a 3ffe::114  -d 202207131800  | jq
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

