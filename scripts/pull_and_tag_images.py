# scripts/pull_and_tag_images.py
import subprocess
import sys

images = [
    ("confluentinc/cp-zookeeper:7.5.0", "docker.m.daocloud.io/confluentinc/cp-zookeeper:7.5.0"),
    ("confluentinc/cp-kafka:7.5.0", "docker.m.daocloud.io/confluentinc/cp-kafka:7.5.0"),
    ("prefecthq/prefect:2.14.0-python3.10", "docker.m.daocloud.io/prefecthq/prefect:2.14.0-python3.10"),
    ("qdrant/qdrant:latest", "docker.m.daocloud.io/qdrant/qdrant:latest"),
    ("redis:7-alpine", "docker.m.daocloud.io/redis:7-alpine"),
    ("prom/prometheus:latest", "docker.m.daocloud.io/prom/prometheus:latest"),
    ("grafana/grafana:latest", "docker.m.daocloud.io/grafana/grafana:latest"),
]

print("Starting to pull and tag images from mirror...")
for orig, mirror in images:
    print(f"\nPulling {mirror} ...")
    ret = subprocess.run(["docker", "pull", mirror])
    if ret.returncode != 0:
        print(f"Error pulling {mirror}")
        sys.exit(1)
        
    print(f"Tagging {mirror} -> {orig} ...")
    ret = subprocess.run(["docker", "tag", mirror, orig])
    if ret.returncode != 0:
        print(f"Error tagging {mirror} to {orig}")
        sys.exit(1)

print("\nAll images successfully pulled and tagged!")
