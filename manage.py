#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    # if os.environ.get("DJANGO_SETTINGS_MODULE")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "deployerweb.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
