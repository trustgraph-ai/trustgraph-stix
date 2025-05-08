
FROM docker.io/fedora:40 AS base

ENV PIP_BREAK_SYSTEM_PACKAGES=1

RUN dnf install -y python3 python3-pip python3-wheel

# ----------------------------------------------------------------------------
# Build a container which contains the built Python packages.  The build
# creates a bunch of left-over cruft, a separate phase means this is only
# needed to support package build
# ----------------------------------------------------------------------------

FROM base AS build

COPY README.md setup.py /root/build/trustgraph-stix/
COPY scripts /root/build/trustgraph-stix/scripts/
COPY trustgraph_stix/ /root/build/trustgraph-stix/trustgraph_stix/

WORKDIR /root/build/

RUN pip3 wheel -w /root/wheels/ --no-deps ./trustgraph-stix/

# ----------------------------------------------------------------------------
# Finally, the target container.  Start with base and add the package.
# ----------------------------------------------------------------------------

FROM base

COPY --from=build /root/wheels /root/wheels

RUN \
    pip3 install --no-cache-dir trustgraph-base && \
    pip3 install --no-cache-dir /root/wheels/trustgraph_stix-* && \
    rm -rf /root/wheels

WORKDIR /

