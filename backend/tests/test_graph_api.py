"""Integration tests for Graph API endpoints."""


class TestGraphBuild:
    def test_build_returns_task_id(self, client):
        resp = client.post("/api/graph/build")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["task_id"].startswith("demo-graph-")
        assert data["status"] == "building"

    def test_task_status_starts_building(self, client):
        build = client.post("/api/graph/build").get_json()
        task_id = build["task_id"]
        resp = client.get(f"/api/graph/task/{task_id}")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "building"
        assert 0 <= data["progress"] <= 100
        assert "message" in data

    def test_task_status_unknown_id_auto_creates(self, client):
        resp = client.get("/api/graph/task/unknown-task-id")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["status"] == "building"

    def test_task_completes_after_skip(self, client):
        build = client.post("/api/graph/build").get_json()
        task_id = build["task_id"]
        client.post("/api/demo/skip/graph")
        resp = client.get(f"/api/graph/task/{task_id}")
        data = resp.get_json()["data"]
        assert data["status"] == "completed"
        assert data["progress"] == 100
        assert "result" in data
        assert data["result"]["graph_id"] == task_id


class TestGraphData:
    def test_graph_data_returns_nodes_and_edges(self, client):
        resp = client.get("/api/graph/data/any-graph-id")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["node_count"] == len(data["nodes"])
        assert data["edge_count"] == len(data["edges"])
        assert data["node_count"] == 55  # 15 personas + 20 topics + 10 relationships + 10 companies

    def test_graph_nodes_have_required_fields(self, client):
        data = client.get("/api/graph/data/test-graph").get_json()["data"]
        node = data["nodes"][0]
        assert "uuid" in node
        assert "name" in node
        assert "labels" in node
        assert "summary" in node

    def test_graph_edges_have_required_fields(self, client):
        data = client.get("/api/graph/data/test-graph").get_json()["data"]
        edge = data["edges"][0]
        assert "uuid" in edge
        assert "source_node_uuid" in edge
        assert "target_node_uuid" in edge
        assert "name" in edge
        assert "fact" in edge


class TestGraphStubs:
    def test_graph_project_get(self, client):
        resp = client.get("/api/graph/project/proj-1")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["project_id"] == "proj-1"

    def test_graph_project_list(self, client):
        resp = client.get("/api/graph/project/list")
        assert resp.status_code == 200
        assert "projects" in resp.get_json()["data"]

    def test_graph_project_delete(self, client):
        resp = client.delete("/api/graph/project/proj-1")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["deleted"] is True

    def test_graph_project_reset(self, client):
        resp = client.post("/api/graph/project/proj-1/reset")
        assert resp.status_code == 200
        assert resp.get_json()["data"]["reset"] is True

    def test_graph_ontology_generate(self, client):
        resp = client.post("/api/graph/ontology/generate")
        assert resp.status_code == 200

    def test_graph_tasks_list(self, client):
        resp = client.get("/api/graph/tasks")
        assert resp.status_code == 200

    def test_graph_delete(self, client):
        resp = client.delete("/api/graph/delete/graph-1")
        assert resp.status_code == 200
