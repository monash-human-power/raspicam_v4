# Notes
> Just some notes while we are developing on V4

## 03/08/24
In the data mqtt class we've removed the exception handler in the functions on connect and on data messafe
commented sections were removed:
```
    def on_data_message(self, client, userdata, msg):
        # with self.exception_handler:
        payload = msg.payload.decode("utf-8")
        self.load_data(msg.topic, payload)

    def _on_connect(self, client, userdata, flags, rc):
        print("start on connect method in data mqtt")
        self.subscribe_to_topic_list(self.get_topics())
        # fucking around
        # with self.exception_handler:
        #     self.on_connect(client, userdata, flags, rc)
        print("Connected with rc , listening to topics: {}".format(rc))
```

It lets us actually see the data from mqtt for the wireless module topics as the exception_handler (defined in camera_error_handler.py) only hancles exceptions for camera feed, thus it only really has use in Overlay which handles mqtting for the camera feed :D