# -*- coding: utf-8 -*-
#!/usr/bin/env python3
from Url import Url
import time


def main():
    u = Url()
    last_update_id = ''

    while True:
        print("Updates")
        updates = u.get_updates(last_update_id)

        print(updates)

        if len(updates['result']) > 0:
            last_update_id = u.get_last_update_id(updates) + 1
            u.handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
