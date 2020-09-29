import hashlib
import json
import logging
from itertools import starmap


class DifferenceLogger(object):
    @staticmethod
    def log_diff(
        subject, from_config, from_server, only_changed=False, hide_entries=None
    ):
        # Simple function to create strings for values which should be hidden
        # example: <secret b2c1a982>
        hide = lambda s: "<secret {}>".format(
            hashlib.sha256(s.encode("utf-8"), usedforsecurity=True).hexdigest()[:8]
        )

        # Compose values in list of `[key, from_config, from_server]``
        changes = [
            [k, json.dumps(from_server.get(k, "???")), json.dumps(v)]
            for k, v in from_config.items()
        ]

        # Remove unchanged if needed
        if only_changed:
            changes = filter(lambda i: i[1] != i[2], changes)

        # Hide secrets
        if hide_entries:
            changes = list(
                map(
                    lambda i: [i[0], hide(i[1]), hide(i[2])]
                    if i[0] in hide_entries
                    else i,
                    changes,
                )
            )

        # calculate field size for nice formatting
        max_key_len = str(max(map(lambda i: len(i[0]), changes)))
        max_val_1 = str(max(map(lambda i: len(i[1]), changes)))
        max_val_2 = str(max(map(lambda i: len(i[2]), changes)))

        # generate placeholders for output pattern: `     value: before  => after   `
        pattern = (
            "{:>" + max_key_len + "}: {:<" + max_val_1 + "} => {:<" + max_val_2 + "}"
        )

        # create string
        text = "{subject}:\n{diff}".format(
            subject=subject, diff="\n".join(starmap(pattern.format, changes))
        )
        logging.info(text)
