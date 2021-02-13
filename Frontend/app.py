from flask import Flask
from flask import request, render_template
import requests

app = Flask(__name__)


@app.route('/', methods=["GET", "POST"])
def index():
    return render_template("home.html")


@app.route('/pipe', methods=["GET", "POST"])
def pipe():
    data = request.form.get("data")
    payload = {}
    headers = {}
    url = "http://127.0.0.1:4000/autocomplete?query=" + str(data)
    response = requests.request("GET", url, headers=headers, data=payload)
    return response.json()


@app.route('/json', methods=["GET", "POST"])
def json():
    import json
    from query_parser.elasticsearch import ElasticsearchQueryBuilder
    from query_parser.parser import parser
    from query_parser.elasticsearch import SchemaAnalyzer
    f = open("/home/mis/projects/autocomplete/courtcase_template.json")
    MESSAGES_SCHEMA = json.load(f)["template"]
    schema_analizer = SchemaAnalyzer(MESSAGES_SCHEMA)
    message_es_builder = ElasticsearchQueryBuilder(**schema_analizer.query_builder_options())

    data = request.form.get("data")
    tree = parser.parse(data)
    query = message_es_builder(tree)
    payload = {
      "_source": {
        "includes": [
            "case_name",
            "case_id",
            "case_number",
            "filing_date",
            "inner_hits",
            "highlight",
            "last_fetch_date_with_updates"
        ]
      },
      "size": 10,
      "track_total_hits": True,
      "query": query,
      "highlight": {
        "pre_tags": ["<b>"],
        "post_tags": ["</b>"],
        "fields": {
            "docket.text": {},
            "case_name": {}
        }
      },
        "sort": {
            "filing_date": "desc"
        }
    }

    response = requests.get(url="http://10.83.94.249:9200/all_courtcases/_search", data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'})
    return get_response(response.json())


def get_response(data):
    response = {
        "result": [],
        "items_per_page": 1,
        "page": 1,
        "total_matches": data["hits"]["total"]["value"]
    }

    for case_dict in data["hits"]["hits"]:
        case = {
            "case_name": case_dict["_source"]["case_name"],
            "case_number": case_dict["_source"]["case_number"],
            "filing_date": case_dict["_source"]["filing_date"],
            "last_fetch_date_with_updates": case_dict["_source"]["last_fetch_date_with_updates"],
            "matches": case_dict["highlight"] if case_dict.get("highlight") else "",
            "url": f"https://api.unicourt.com/case/CASE_iHoKn66p8dgTC",
            "parties": [],
            "attorneys": [],
            "judges": [],
            "dockets": []
        }
        inner_hits = case_dict.get("inner_hits")
        if inner_hits:
            for key, value in inner_hits.items():
                inner_hit_dict_list = value["hits"]["hits"]
                for inner_hit_dict in inner_hit_dict_list:
                    if inner_hit_dict["_nested"]["field"] == 'party':
                        party_dict = {
                            "full_name": inner_hit_dict["_source"]["name"],
                            "party_type": inner_hit_dict["_source"]["party_type"]["name"],
                            "representation_type": inner_hit_dict["_source"]["representation"]["name"],
                            "url": f"https://api.unicourt.com/case/CASE_iHoKn66p3bkcN/parties/CPTY_iHoKn66p8dgTC",
                            "matches": []
                        }
                        for match_field, snippet_list in inner_hit_dict["highlight"].items():
                            if match_field == "party.name":
                                attribute = "full_name"
                            elif match_field == "party.party_type.name":
                                attribute = "party_type"
                            elif match_field == "party.representation.name":
                                attribute = "representation_type"
                            party_dict["matches"].append({
                                "highlight_snippet": snippet_list[0],
                                "attribute": attribute
                            })
                        case["parties"].append(party_dict)
                    elif inner_hit_dict["_nested"]["field"] == 'attorney':
                        attorney_dict = {
                            "full_name": inner_hit_dict["_source"]["name"],
                            "attorney_type": inner_hit_dict["_source"]["attorney_type"]["name"],
                            "firm":  inner_hit_dict["_source"]["firm"],
                            "url": f"https://api.unicourt.com/case/CASE_iHoKn66p3bkcN/attorneys/CATY_iHoKn66p8dgTC",
                            "matches": []
                        }
                        for match_field, snippet_list in inner_hit_dict["highlight"].items():
                            if match_field == "attorney.name":
                                attribute = "full_name"
                            elif match_field == "attorney.attorney_type.name":
                                attribute = "attorney_type"
                            elif match_field == "attorney.firm":
                                attribute = "firm"
                            attorney_dict["matches"].append({
                                "highlight_snippet": snippet_list[0],
                                "attribute": attribute
                            })
                        case["attorneys"].append(attorney_dict)
                    elif inner_hit_dict["_nested"]["field"] == 'judge':
                        judge_dict = {
                            "full_name": inner_hit_dict["_source"]["name"],
                            "judge_type": inner_hit_dict["_source"]["judge_type"]["name"],
                            "url": f"https://api.unicourt.com/case/CASE_iHoKn66p3bkcN/judges/CJDG_iHoKn66p8dgTC",
                            "matches": []
                        }
                        for match_field, snippet_list in inner_hit_dict["highlight"].items():
                            if match_field == "judge.name":
                                attribute = "full_name"
                            elif match_field == "judge.judge_type.name":
                                attribute = "judge_type"
                            judge_dict["matches"].append({
                                "highlight_snippet": snippet_list[0],
                                "attribute": attribute
                            })
                        case["judges"].append(judge_dict)
                    elif inner_hit_dict["_nested"]["field"] == 'docket':
                        docket_dict = {
                            "text": inner_hit_dict["_source"]["text"],
                            "docket_entry_date": inner_hit_dict["_source"]["action_date"],
                            "url": f"https://api.unicourt.com/case/CASE_iHoKn66p3bkcN/dockets/CDKT_iHoKn66p8dgTC",
                            "highlight_snippet": inner_hit_dict["highlight"]["docket.text"][0]
                        }
                        case["dockets"].append(docket_dict)
                        # case["highlight_snippet"] = ""
        response["result"].append(case)
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5000)
