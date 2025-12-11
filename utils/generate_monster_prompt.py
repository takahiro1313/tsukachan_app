def generate_monster_prompt(
    filtered_row: dict,
    mapping_rows: list[dict],
    description: str
) -> str:
    """
    フィルタ済みのキャラクターステータスと species_mapping を使って
    モンスター生成用プロンプトを返す関数
    """

    # ステータスソート
    sorted_params = sorted(filtered_row.items(), key=lambda x: x[1], reverse=True)
    top1, top2, top3 = sorted_params[0], sorted_params[1], sorted_params[2]
    top1_name, top2_name, top3_name = top1[0], top2[0], top3[0]

    # 種族判定（within_20percentは別関数にしてもいいし、ここに残してもOK）
    def within_20percent(a, b):
        return abs(a - b) / max(a, b) <= 0.2

    chosen = None
    if within_20percent(top1[1], top2[1]):
        for r in mapping_rows:
            param_list = r["parameter"].split("_")
            if len(param_list) == 2 and {top1_name, top2_name} <= set(param_list):
                chosen = r
                break

    if not chosen and within_20percent(top1[1], top2[1]) and within_20percent(top1[1], top3[1]):
        for r in mapping_rows:
            param_list = r["parameter"].split("_")
            if len(param_list) == 3 and {top1_name, top2_name, top3_name} <= set(param_list):
                chosen = r
                break

    if not chosen:
        chosen = next(r for r in mapping_rows if r["parameter"] == top1_name)

    species, appearance, battle_style = chosen["species"], chosen["Appearance"], chosen["battle_style"]
    type_val = next(r["type"] for r in mapping_rows if r["parameter"] == top2_name)
    color_val = next(r["color"] for r in mapping_rows if r["parameter"] == top3_name)

    # 進化段階判定
    if top1[1] >= 500:
        stage = chosen["legend"]
        stage_design = "荘厳で厳か、畏怖と尊厳を放つ超越的で崇高なデザインにしてください。"
    elif top1[1] >= 150:
        stage = chosen["adult"]
        stage_design = "成熟した風格、自信と落ち着きを兼ね備えた雰囲気を持つデザインにしてください。"
    else:
        stage = chosen["child"]
        stage_design = "愛嬌があって可愛らしいデザインにしてください。"

    # 英語キーを日本語に変換する辞書
    status_labels = {
        "attack": "攻撃", "defense": "防御", "agility": "素早さ", "charm": "魅力",
        "intelligence": "知力", "concentration": "集中", "magic": "魔力",
        "dexterity": "器用さ", "love": "愛", "luck": "運"
    }

    # ステータス整形
    status_text = "\n".join([
        f"{status_labels.get(k, k)}: {v}"
        for k, v in filtered_row.items()
    ])

    # プロンプト生成
    prompt_image = f"""
あなたはモンスターのデザイナーです。
以下の指示に従って1体のモンスターのイラストを生成してください。

・ベースデザイン: {stage}
・全体的なデザイン指示: {stage_design}
・色: {type_val}。さらに体全体の30%程度に {color_val} を取り入れてください。
・除外：文字、ロゴ、人間、低解像度、歪み。
・背景：荒廃した神殿
・このキャラクターの特徴は以下の通りです：
{description}

"""

    # 名前生成用プロンプト
    prompt_name = f"""
あなたはファンタジーゲームのキャラクターデザイナーです。
以下の特徴を持つモンスターに、かっこいい名前を付けてください。

⚠️ 出力条件（厳守）：
- 神話的で詩的な響き
- 出力は名前のみ

このキャラクターの特徴は以下の通りです：
{description}

種族: {species}（外見: {appearance}, 戦闘スタイル: {battle_style}）
タイプ: {type_val}
色: 主な色はタイプから連想してください。さらに体全体の30%程度に {color_val} を取り入れてください。
ベースデザイン: {stage}
全体的なデザイン指示: {stage_design}
"""



    return prompt_image.strip(), prompt_name.strip()