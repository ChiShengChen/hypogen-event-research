import json
from pathlib import Path

from fastapi.testclient import TestClient

from research_app.adapters import ScenarioCodex
from research_app.api import create_app
from research_app.hypothesis_tree import TreeDraft
from research_app.store import Store, encode


class BranchRecorder(ScenarioCodex):
    def __init__(self, report):
        super().__init__()
        self.report = report
        self.contexts = []

    def _generate(self, schema, instruction, context):
        assert schema is TreeDraft and "a premise to test" in instruction
        self.contexts.append(context)
        sample = self.report["stance_cases"][0]["cases"][0]
        candidate = sample | {"stance": "bull", "title": "訂單續航",
                              "mechanism": f"長期合約出貨機制 {len(self.contexts)}"}
        if context["mode"] == "fanout":
            return schema(hypotheses=[
                candidate,
                candidate | {"stance": "bear", "mechanism": "資本支出延後", "title": "空方機制"},
                candidate | {"stance": "wait", "mechanism": "缺來源", "evidence_ids": ["asml-q4:actual"]},
            ], gaps=[])
        return schema(hypotheses=[candidate], gaps=[])


def test_hypothesis_tree_preserves_custom_premise_across_deep_branches(tmp_path):
    report = json.loads(Path("docs/guidance-table/scenario-draft.json").read_text())
    store = Store(tmp_path / "hypotheses.sqlite")
    with store.connection() as db:
        db.execute("INSERT INTO runs VALUES ('test', 'run', 'key', '{}')")
        db.execute("INSERT INTO revisions VALUES ('test', 1, NULL, ?)", (encode(report),))
    store.save_child("test", 1, report)
    adapter = BranchRecorder(report)
    url = "/reports/test/revisions/1/hypothesis-tree"
    with TestClient(create_app(store, adapter)) as client:
        nodes = client.get(url).json()["nodes"]
        assert {node["id"] for node in nodes if node["parent_id"] == "root"} == {
            "stance:bull", "stance:base", "stance:bear", "stance:wait",
        }

        def extend(parent, mode, question, **extra):
            response = client.post(url, json={"parent_id": parent, "mode": mode, "question": question, **extra})
            assert response.status_code == 200, response.text
            return response.json()["nodes"]

        group, bull, bear = extend("root", "fanout", "客戶延後驗收可能帶來哪些結果？")
        assert [bull["stance"], bear["stance"]] == ["多方", "空方"]
        assert bull["parent_id"] == bear["parent_id"] == group["id"]
        assert group["gaps"] and "asml-q4:actual" not in {row["id"] for row in adapter.contexts[0]["evidence"]}
        custom, current = extend(bear["id"], "custom", "驗收延後但總需求持平", stance="驗收節奏")
        assert custom["parent_id"] == bear["id"] and current["stance"] == "驗收節奏"
        for turn in range(8):
            step, current = extend(current["id"], "followup", f"追問 {turn} 可驗證預測")
            assert current["parent_id"] == step["id"] and current["stance"] == "驗收節奏"
        final_context = adapter.contexts[-1]
        assert len(final_context["ancestor_context"]) == 6
        assert final_context["analyst_premise"] == "驗收延後但總需求持平"
        assert client.post(url, json={"parent_id": "missing", "mode": "followup", "question": "追問"}).status_code == 404
        assert client.post(url.replace("/1/", "/2/"), json={
            "parent_id": current["id"], "mode": "followup", "question": "追問",
        }).status_code == 404
        assert client.get("/reports/test/revisions/1").json()["stance_cases"] == report["stance_cases"]
    reloaded = Store(store.path).hypothesis_tree("test", 1)["nodes"]
    assert {node["id"] for node in reloaded} >= {custom["id"], current["id"], bear["id"]}
