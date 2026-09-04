# Tells Cloud Run's buildpacks how to start this app. Buildpacks can install
# dependencies and make the package importable from pyproject.toml alone, but
# have no way to infer which command should actually launch the service, so
# this file bridges that gap.
#
# --host 0.0.0.0 : accept connections from outside the container, not just
#                  localhost (127.0.0.1 only works for local development).
# --port $PORT   : Cloud Run assigns the port dynamically at runtime via this
#                  env var; it must not be hardcoded.

web: uvicorn pathology_extraction.api:app --host 0.0.0.0 --port $PORT