"""
Test CLI Utils
"""
import json
import os
import pytest
from click.testing import CliRunner

from kgx.cli.cli_utils import validate, neo4j_upload, neo4j_download, transform, merge
from kgx.cli import cli, get_input_file_types, graph_summary, get_report_format_types
from tests import RESOURCE_DIR, TARGET_DIR
from tests.unit import (
    check_container,
    clean_slate,
    CONTAINER_NAME,
    DEFAULT_NEO4J_URL,
    DEFAULT_NEO4J_USERNAME,
    DEFAULT_NEO4J_PASSWORD
)


def test_get_file_types():
    """
    Test get_file_types method.
    """
    file_types = get_input_file_types()
    assert "tsv" in file_types
    assert "nt" in file_types
    assert "json" in file_types
    assert "obojson" in file_types


def test_get_report_format_types():
    """
    Test get_report_format_types method.
    """
    format_types = get_report_format_types()
    assert "yaml" in format_types
    assert "json" in format_types


@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_graph_summary_wrapper():
    output = os.path.join(TARGET_DIR, "graph_stats3.yaml")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "graph-summary",
            "-i", "tsv",
            "-o", output,
            os.path.join(RESOURCE_DIR, "graph_nodes.tsv")
        ]
    )
    assert result.exit_code == 0

@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_graph_summary_wrapper_error():
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "graph_stats3.yaml")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "graph-summary",
            "-i", "tsv",
            "-o", output,
            inputs
        ]
    )
    assert result.exit_code == 1

@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_transform_wrapper():
    """
        Transform graph from TSV to JSON.
        """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "grapht.json")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "transform",
            "-i", "tsv",
            "-o", output,
            "-f", "json",
            inputs
        ]
    )

    assert result.exit_code == 1

@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_merge_wrapper():

    """
    Transform from test merge YAML.
    """
    merge_config = os.path.join(RESOURCE_DIR, "test-merge.yaml")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "merge",
            "--merge-config", merge_config
        ]
    )

    assert result.exit_code == 0
    assert os.path.join(TARGET_DIR, "merged-graph_nodes.tsv")
    assert os.path.join(TARGET_DIR, "merged-graph_edges.tsv")
    assert os.path.join(TARGET_DIR, "merged-graph.json")


@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_merge_wrapper_error():

    """
    Transform from test merge YAML.
    """
    merge_config = os.path.join(RESOURCE_DIR, "test-merge.yaml")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "merge"
        ]
    )

    assert result.exit_code == 2


def test_kgx_graph_summary():
    """
    Test graph summary, where the output report type is kgx-map.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "graph_stats1.yaml")
    summary_stats = graph_summary(
        inputs,
        "tsv",
        None,
        output,
        node_facet_properties=["provided_by"],
        edge_facet_properties=["aggregator_knowledge_source"],
        report_type="kgx-map"
    )

    assert os.path.exists(output)
    assert summary_stats
    assert "node_stats" in summary_stats
    assert "edge_stats" in summary_stats
    assert summary_stats["node_stats"]["total_nodes"] == 512
    assert "biolink:Gene" in summary_stats["node_stats"]["node_categories"]
    assert "biolink:Disease" in summary_stats["node_stats"]["node_categories"]
    assert summary_stats["edge_stats"]["total_edges"] == 539
    assert "biolink:has_phenotype" in summary_stats["edge_stats"]["predicates"]
    assert "biolink:interacts_with" in summary_stats["edge_stats"]["predicates"]


def test_meta_knowledge_graph_as_json():
    """
    Test graph summary, where the output report type is a meta-knowledge-graph,
    with results output as the default JSON report format type.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "meta-knowledge-graph.json")
    summary_stats = graph_summary(
        inputs,
        "tsv",
        None,
        output,
        report_type="meta-knowledge-graph",
        node_facet_properties=["provided_by"],
        edge_facet_properties=["aggregator_knowledge_source"],
        graph_name="Default Meta-Knowledge-Graph",
    )

    assert os.path.exists(output)
    assert summary_stats
    assert "nodes" in summary_stats
    assert "edges" in summary_stats
    assert "name" in summary_stats
    assert summary_stats["name"] == "Default Meta-Knowledge-Graph"


def test_meta_knowledge_graph_as_yaml():
    """
    Test graph summary, where the output report type is a meta-knowledge-graph,
    with results output as the YAML report output format type.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "meta-knowledge-graph.yaml")
    summary_stats = graph_summary(
        inputs,
        "tsv",
        None,
        output,
        report_type="meta-knowledge-graph",
        node_facet_properties=["provided_by"],
        edge_facet_properties=["aggregator_knowledge_source"],
        report_format="yaml"
    )

    assert os.path.exists(output)
    assert summary_stats
    assert "nodes" in summary_stats
    assert "edges" in summary_stats


def test_meta_knowledge_graph_as_json_streamed():
    """
    Test graph summary processed in stream mode, where the output report type
    is meta-knowledge-graph, output as the default JSON report format type.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "meta-knowledge-graph-streamed.json")
    summary_stats = graph_summary(
        inputs=inputs,
        input_format="tsv",
        input_compression=None,
        output=output,
        report_type="meta-knowledge-graph",
        node_facet_properties=["provided_by"],
        edge_facet_properties=["aggregator_knowledge_source"],
        stream=True,
    )

    assert os.path.exists(output)
    assert summary_stats
    assert "nodes" in summary_stats
    assert "edges" in summary_stats


def test_validate_exception_triggered_error_exit_code():
    """
    Test graph validate error exit code.
    """
    test_input = os.path.join(RESOURCE_DIR, "graph_nodes.tsv")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "validate",
            "-i", "tsv",
            "-b not.a.semver",
            test_input
        ]
    )
    assert result.exit_code == 1


@pytest.mark.parametrize(
    "query",
    [
        ("graph_nodes.tsv", 0),
        ("test_nodes.tsv", 1),
    ],
)
def test_validate_parsing_triggered_error_exit_code(query):
    """
    Test graph validate error exit code.
    """
    test_input = os.path.join(RESOURCE_DIR, query[0])
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "validate",
            "-i", "tsv",
            test_input
        ]
    )
    assert result.exit_code == query[1]


def test_validate_non_streaming():
    """
    Test graph validation.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "valid.json"),
    ]
    output = os.path.join(TARGET_DIR, "validation.log")
    errors = validate(
        inputs=inputs,
        input_format="json",
        input_compression=None,
        output=output,
        stream=False,
        biolink_release="2.1.0",
    )
    assert os.path.exists(output)
    assert len(errors) == 0


def test_validate_streaming():
    """
    Test graph validation.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "valid.json"),
    ]
    output = os.path.join(TARGET_DIR, "validation.log")
    errors = validate(
        inputs=inputs,
        input_format="json",
        input_compression=None,
        output=output,
        stream=True,
        biolink_release="2.1.0",
    )
    assert os.path.exists(output)
    assert len(errors) == 0


@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_neo4j_upload(clean_slate):
    """
    Test upload to Neo4j.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    # upload
    t = neo4j_upload(
        inputs,
        "tsv",
        None,
        uri=DEFAULT_NEO4J_URL,
        username=DEFAULT_NEO4J_USERNAME,
        password=DEFAULT_NEO4J_PASSWORD,
        stream=False,
    )
    assert t.store.graph.number_of_nodes() == 512
    assert t.store.graph.number_of_edges() == 531


@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_neo4j_download_wrapper(clean_slate):
    output = os.path.join(TARGET_DIR, "neo_download2")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "neo4j-download",
            "-l", DEFAULT_NEO4J_URL,
            "-o", output,
            "-f", "tsv",
            "-u", DEFAULT_NEO4J_USERNAME,
            "-p", DEFAULT_NEO4J_PASSWORD,
        ]
    )

    assert os.path.exists(f"{output}_nodes.tsv")
    assert os.path.exists(f"{output}_edges.tsv")

    assert result.exit_code == 0

@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_download_exception_triggered_error_exit_code():
    """
    Test graph download error exit code.
    """

    output = os.path.join(TARGET_DIR, "neo_download")
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "neo4j-download",
            "-l", DEFAULT_NEO4J_URL,
            "-o", output,
            "-f", "tsv",
            "-u", "not a user name",
            "-p", DEFAULT_NEO4J_PASSWORD,
        ]
    )
    assert result.exit_code == 1

@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_neo4j_upload_wrapper(clean_slate):
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "neo4j-upload",
            "--input-format", "tsv",
            "--uri", DEFAULT_NEO4J_URL,
            "--username", DEFAULT_NEO4J_USERNAME,
            "--password", DEFAULT_NEO4J_PASSWORD,
            os.path.join(RESOURCE_DIR, "graph_nodes.tsv")
        ]
    )

    assert result.exit_code == 0


@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_neo4j_upload_wrapper_error(clean_slate):
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "neo4j-upload",
            "-i", "tsv",
            "inputs", "not_a_path"
            "-u", "not a user",
            "-p", DEFAULT_NEO4J_PASSWORD,
        ]
    )

    assert result.exit_code == 2

@pytest.mark.skip()
@pytest.mark.skipif(
    not check_container(), reason=f"Container {CONTAINER_NAME} is not running"
)
def test_neo4j_download(clean_slate):
    """
    Test download from Neo4j.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "neo_download")
    # upload
    t1 = neo4j_upload(
        inputs=inputs,
        input_format="tsv",
        input_compression=None,
        uri=DEFAULT_NEO4J_URL,
        username=DEFAULT_NEO4J_USERNAME,
        password=DEFAULT_NEO4J_PASSWORD,
        stream=False,
    )
    t2 = neo4j_download(
        uri=DEFAULT_NEO4J_URL,
        username=DEFAULT_NEO4J_USERNAME,
        password=DEFAULT_NEO4J_PASSWORD,
        output=output,
        output_format="tsv",
        output_compression=None,
        stream=False,
    )
    assert os.path.exists(f"{output}_nodes.tsv")
    assert os.path.exists(f"{output}_edges.tsv")
    assert t1.store.graph.number_of_nodes() == t2.store.graph.number_of_nodes()
    assert t1.store.graph.number_of_edges() == t2.store.graph.number_of_edges()


def test_transform1():
    """
    Transform graph from TSV to JSON.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "graph.json")
    knowledge_sources = [
        ("aggregator_knowledge_source", "True"),
    ]
    transform(
        inputs=inputs,
        input_format="tsv",
        input_compression=None,
        output=output,
        output_format="json",
        output_compression=None,
        knowledge_sources=knowledge_sources,
    )
    assert os.path.exists(output)
    data = json.load(open(output, "r"))
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 512
    assert len(data["edges"]) == 531
    for e in data["edges"]:
        if e["subject"] == "HGNC:10848" and e["object"] == "HGNC:20738":
            assert "aggregator_knowledge_source" in e
            assert "infores:string" in e["aggregator_knowledge_source"]
            assert "infores:biogrid" in e["aggregator_knowledge_source"]
            break


def test_transform_knowledge_source_suppression():
    """
    Transform graph from TSV to JSON.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "graph.json")
    knowledge_sources = [
        ("aggregator_knowledge_source", "False"),
        ("knowledge_source", "False"),
    ]
    transform(
        inputs=inputs,
        input_format="tsv",
        input_compression=None,
        output=output,
        output_format="json",
        output_compression=None,
        knowledge_sources=knowledge_sources,
    )
    assert os.path.exists(output)
    data = json.load(open(output, "r"))
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 512
    assert len(data["edges"]) == 531
    for e in data["edges"]:
        if e["subject"] == "HGNC:10848" and e["object"] == "HGNC:20738":
            assert "aggregator_knowledge_source" not in e
            assert "knowledge_source" not in e
            break


def test_transform_knowledge_source_rewrite():
    """
    Transform graph from TSV to JSON.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "graph.json")
    knowledge_sources = [
        ("aggregator_knowledge_source", "string,string database"),
        ("aggregator_knowledge_source", "go,gene ontology"),
    ]
    transform(
        inputs=inputs,
        input_format="tsv",
        input_compression=None,
        output=output,
        output_format="json",
        output_compression=None,
        knowledge_sources=knowledge_sources,
    )
    assert os.path.exists(output)
    data = json.load(open(output, "r"))
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 512
    assert len(data["edges"]) == 531
    for e in data["edges"]:
        if e["subject"] == "HGNC:10848" and e["object"] == "HGNC:20738":
            assert "aggregator_knowledge_source" in e
            assert "infores:string-database" in e["aggregator_knowledge_source"]
        if e["subject"] == "HGNC:10848" and e["object"] == "GO:0005576":
            assert "aggregator_knowledge_source" in e
            assert "infores:gene-ontology" in e["aggregator_knowledge_source"]


def test_transform_knowledge_source_rewrite_with_prefix():
    """
    Transform graph from TSV to JSON.
    """
    inputs = [
        os.path.join(RESOURCE_DIR, "graph_nodes.tsv"),
        os.path.join(RESOURCE_DIR, "graph_edges.tsv"),
    ]
    output = os.path.join(TARGET_DIR, "graph.json")
    knowledge_sources = [
        ("aggregator_knowledge_source", "string,string database,new"),
        ("aggregator_knowledge_source", "go,gene ontology,latest"),
    ]
    transform(
        inputs=inputs,
        input_format="tsv",
        input_compression=None,
        output=output,
        output_format="json",
        output_compression=None,
        knowledge_sources=knowledge_sources,
    )
    assert os.path.exists(output)
    data = json.load(open(output, "r"))
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 512
    assert len(data["edges"]) == 531
    for e in data["edges"]:
        if e["subject"] == "HGNC:10848" and e["object"] == "HGNC:20738":
            assert "aggregator_knowledge_source" in e
            assert "infores:new-string-database" in e["aggregator_knowledge_source"]
        if e["subject"] == "HGNC:10848" and e["object"] == "GO:0005576":
            assert "aggregator_knowledge_source" in e
            assert "infores:latest-gene-ontology" in e["aggregator_knowledge_source"]


def test_transform2():
    """
    Transform from a test transform YAML.
    """
    transform_config = os.path.join(RESOURCE_DIR, "test-transform.yaml")
    transform(inputs=None, transform_config=transform_config)
    assert os.path.exists(os.path.join(RESOURCE_DIR, "graph_nodes.tsv"))
    assert os.path.exists(os.path.join(RESOURCE_DIR, "graph_edges.tsv"))


def test_merge1():
    """
    Transform from test merge YAML.
    """
    merge_config = os.path.join(RESOURCE_DIR, "test-merge.yaml")
    merge(merge_config=merge_config)
    assert os.path.join(TARGET_DIR, "merged-graph_nodes.tsv")
    assert os.path.join(TARGET_DIR, "merged-graph_edges.tsv")
    assert os.path.join(TARGET_DIR, "merged-graph.json")


def test_merge2():
    """
    Transform selected source from test merge YAML and
    write selected destinations.
    """
    merge_config = os.path.join(RESOURCE_DIR, "test-merge.yaml")
    merge(merge_config=merge_config, destination=["merged-graph-json"])
    assert os.path.join(TARGET_DIR, "merged-graph.json")
