# `urils.browser` Module

Module can be used to request page content through tor browser

* Start redis container
```
cd redis_conf
docker-compose up 
```

* Start browser workers
```
huey_consumer page_getter.huey -k process -w 4
```

* Import module and request required page
```
from utils.browser import get_html

print(get_html('https://google.com').get(blocking=True))
```


TODO: 
* Clean requirements.txt
* Handle exceptions in worker to close webDriver
* Initiate new tor instance on each webDriver creation