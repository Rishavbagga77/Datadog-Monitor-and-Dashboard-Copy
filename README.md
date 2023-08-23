# Datadog-Monitor-and-Dashboard-Copy
# #!/usr/bin/env python3
"""Usage:
  main.py pull (<type>) [--tag tag]... [--dry-run] [-h]
  main.py push (<type>) [--dry-run] [-h]

Examples:
    Dashboards:
        main.py pull dashboards
        main.py push dashboards

    Synthetic api tests using --tag that only pulls tests if all the defined tags exist on them:
        main.py pull synthetic_api_tests p --tag env:production --tag application:abc
        main.py push synthetic_api_tests

    Run with --dry-run without making any changes to your Datadog account:
        main.py pull dashboards --dry-run
        main.py push dashboards --dry-run
 
    Supported arguments:
    main.py pull|push dashboards|monitors|users|synthetics_api_tests|synthetics_browser_tests|awsaccounts|logpipelines|notebooks (--tag tag) (--dry-run|-h)

    Note. --tag is currently only supported for synthetics_api_tests, synthetics_browser_tests and monitors.

Options:
  -h, --help
  -d, --dry-run
  --tag=<k:v>   Specify a tag in the format key:value
"""
