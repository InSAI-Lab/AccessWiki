#!/usr/bin/env python3
import argparse
import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACT_PATH = (
    ROOT
    / "experiments/formal_v01/fact_sheets/formal_fact_sheets.json"
)
SOURCE_MANIFEST_PATH = ROOT / "topics/formal_source_manifest.json"
OUTPUT_DIR = ROOT / "generated/evidence_html"

HEADINGS = {
    "R1": "车票包含的信息",
    "R2": "按照车票信息乘车",
    "R3": "安全检查和携带物品",
    "R4": "车站导向与信息设施",
    "R5": "身份证检票异常处理",
    "R6": "必要的人工服务",
    "R7": "携带导盲犬乘车",
    "H1": "门诊预约方式",
    "H2": "门诊挂号方式",
    "H3": "候诊和叫号",
    "H4": "门诊缴费方式",
    "H5": "缴费和检查顺序",
    "H6": "特殊检查预约",
    "H7": "西药取药流程",
    "O1": "七日期间的计算",
    "O2": "销售者提供退货信息",
    "O3": "退回商品和保留凭证",
    "O4": "商品、配件和赠品",
    "O5": "商品完好的基本条件",
    "O6": "开包查验和合理调试",
    "O7": "返还商品价款的期限",
    "O8": "退款方式",
    "O9": "退货运费承担",
}

LOCATIONS = {
    "R1": "《铁路旅客运输规程》第四条",
    "R2": "《铁路旅客运输规程》第二十条",
    "R3": "《铁路旅客运输规程》第十七条",
    "R4": "《铁路旅客运输规程》第十九条",
    "R5": "中国铁路12306常见问题：检票进站时闸机不放行",
    "R6": "《铁路旅客运输规程》第二十二条",
    "R7": "《铁路旅客运输规程》第二十二条",
    "H1": "预约挂号部分",
    "H2": "就诊流程第一部分：挂号",
    "H3": "就诊流程第一部分：挂号与候诊",
    "H4": "就诊流程第二部分：缴费",
    "H5": "就诊流程第三部分：相关项目检查",
    "H6": "就诊流程第三部分：相关项目检查",
    "H7": "就诊流程第四部分：取药",
    "O1": "暂行办法第十条",
    "O2": "暂行办法第十一条",
    "O3": "暂行办法第十一条",
    "O4": "暂行办法第十二条",
    "O5": "暂行办法第八条",
    "O6": "暂行办法第八条",
    "O7": "暂行办法第十三条",
    "O8": "暂行办法第十四条",
    "O9": "暂行办法第十八条",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def parse_reference(reference):
    match = re.fullmatch(
        r"(primary|supplementary)\.txt:(\d+)(?:-(\d+))?",
        reference,
    )

    if not match:
        raise ValueError(f"无法解析证据引用：{reference}")

    return (
        match.group(1),
        int(match.group(2)),
        int(match.group(3) or match.group(2)),
    )


def extract_lines(path, start, end):
    lines = path.read_text(encoding="utf-8").splitlines()
    selected = lines[start - 1:end]
    cleaned = []

    for line in selected:
        value = line.strip()

        if not value:
            continue

        if re.fullmatch(r"[—\-–\s]*\d+[—\-–\s]*", value):
            continue

        cleaned.append(re.sub(r"\s+", "", value))

    text = "".join(cleaned)

    if not text:
        raise ValueError(f"证据提取为空：{path}:{start}-{end}")

    return text


def main():
    parser = argparse.ArgumentParser(description="Generate the three formal Evidence HTML pages")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    output_dir = args.output_dir.expanduser().resolve()
    facts = load_json(FACT_PATH)
    source_manifest = load_json(SOURCE_MANIFEST_PATH)

    source_topics = {
        topic["topic_id"]: topic
        for topic in source_manifest["topics"]
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_topics = []

    for topic in facts["formal_topics"]:
        topic_id = topic["topic_id"]
        source_topic = source_topics[topic_id]

        toc = []
        claim_sections = []
        manifest_records = []

        for fact in topic["facts"]:
            fact_id = fact["fact_id"]
            heading = HEADINGS[fact_id]
            anchor = f"claim-{fact_id.lower()}"

            toc.append(
                f'<li><a href="#{anchor}">'
                f'{html.escape(heading)}</a></li>'
            )

            evidence_sections = []

            for index, reference in enumerate(
                fact["evidence"],
                start=1,
            ):
                source_kind, start, end = parse_reference(reference)
                source_path = ROOT / topic[f"{source_kind}_source"]
                evidence_text = extract_lines(
                    source_path,
                    start,
                    end,
                )

                metadata = source_topic.get(
                    f"{source_kind}_source",
                    {},
                )

                source_title = metadata.get(
                    "title",
                    source_path.name,
                )
                organization = metadata.get("organization", "")
                source_url = metadata.get("url", "")

                source_name = html.escape(source_title)

                if organization:
                    source_name += "；" + html.escape(organization)

                if source_url:
                    source_name = (
                        f'<a href="{html.escape(source_url)}">'
                        f'{source_name}</a>'
                    )

                evidence_sections.append(
                    f'''
                    <section class="evidence"
                             aria-labelledby="{anchor}-e{index}">
                      <h3 id="{anchor}-e{index}">
                        原文证据 {index}
                      </h3>
                      <blockquote>
                        {html.escape(evidence_text)}
                      </blockquote>
                      <p>来源：{source_name}</p>
                      <p>
                        位置：{html.escape(LOCATIONS[fact_id])}
                      </p>
                    </section>
                    '''
                )

                manifest_records.append(
                    {
                        "fact_id": fact_id,
                        "reference": reference,
                        "source_file": source_path.relative_to(ROOT).as_posix(),
                        "evidence_text": evidence_text,
                    }
                )

            claim_sections.append(
                f'''
                <section class="claim-section"
                         id="{anchor}"
                         data-claim-id="{fact_id}">
                  <h2>{html.escape(heading)}</h2>
                  <p class="claim">
                    <strong>文档要点：</strong>
                    {html.escape(fact["claim"])}
                  </p>
                  {''.join(evidence_sections)}
                  <p><a href="#evidence-directory">
                    返回证据目录
                  </a></p>
                </section>
                '''
            )

        document = f'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport"
        content="width=device-width, initial-scale=1">
  <title>{html.escape(topic["title_zh"])}：证据核验页面</title>
  <style>
    :root {{
      font-family: system-ui, "Microsoft YaHei", sans-serif;
      font-size: 18px;
      line-height: 1.75;
      color: #111;
      background: #fff;
    }}
    body {{
      max-width: 52rem;
      margin: 0 auto;
      padding: 1rem 1.25rem 4rem;
    }}
    a {{
      color: #0645ad;
      text-underline-offset: 0.15em;
    }}
    a:focus {{
      outline: 3px solid #ffbf47;
      outline-offset: 3px;
    }}
    .skip-link {{
      position: absolute;
      left: -9999px;
    }}
    .skip-link:focus {{
      left: 1rem;
      top: 1rem;
      padding: 0.75rem;
      color: #fff;
      background: #000;
    }}
    h1, h2, h3 {{
      line-height: 1.35;
    }}
    nav, .claim-section {{
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 2px solid #333;
    }}
    .scope {{
      padding: 0.8rem 1rem;
      border-left: 0.35rem solid #555;
      background: #f3f3f3;
    }}
    .claim {{
      font-weight: 600;
    }}
    .evidence {{
      margin: 1.25rem 0;
      padding: 0.5rem 1rem 1rem;
      background: #f7f7f7;
    }}
    blockquote {{
      margin: 0.75rem 0;
      padding-left: 1rem;
      border-left: 0.3rem solid #555;
    }}
  </style>
</head>
<body>
  <a class="skip-link" href="#main-content">
    跳到主要内容
  </a>

  <header>
    <h1>{html.escape(topic["title_zh"])}：证据核验页面</h1>
    <p>
      本页面将音频中的文档要点与原始来源证据逐项对应。
      可使用读屏软件按标题或链接导航。
    </p>
    <p class="scope">
      <strong>材料范围：</strong>
      {html.escape(topic["scope_note"])}
    </p>
  </header>

  <nav id="evidence-directory" aria-label="本页证据目录">
    <h2>证据目录</h2>
    <ol>{''.join(toc)}</ol>
  </nav>

  <main id="main-content" tabindex="-1">
    {''.join(claim_sections)}
  </main>
</body>
</html>
'''

        output_path = output_dir / f"{topic_id}_evidence.html"
        output_path.write_text(document, encoding="utf-8")

        rendered = output_path.read_text(encoding="utf-8")
        claim_count = rendered.count('class="claim-section"')
        evidence_count = rendered.count('class="evidence"')

        if claim_count != len(topic["facts"]):
            raise ValueError(
                f"{topic_id} claim数量异常：{claim_count}"
            )

        if evidence_count < len(topic["facts"]):
            raise ValueError(
                f"{topic_id} evidence数量异常：{evidence_count}"
            )

        manifest_topics.append(
            {
                "topic_id": topic_id,
                "html_file": output_path.name,
                "claim_count": claim_count,
                "evidence_count": evidence_count,
                "records": manifest_records,
            }
        )

        print(
            f"{topic_id}: "
            f"{claim_count} claims, "
            f"{evidence_count} evidence blocks"
        )

    manifest_path = (
        output_dir / "formal_evidence_html_manifest.json"
    )

    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "purpose": "formal_blv_experiment",
                "shared_between_conditions": ["B2", "P"],
                "nvda_manual_qc": "not_performed",
                "topics": manifest_topics,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"MANIFEST={manifest_path}")
    print("FORMAL_EVIDENCE_HTML_OK")


if __name__ == "__main__":
    main()
