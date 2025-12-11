def update_evolution(row: dict, decrement: int = 1000) -> dict:
    import streamlit as st
    from supabase import create_client, Client

    # Supabase設定
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    """
    characterテーブルの evolution を減算し、
    evolution_count をインクリメントして更新
    row: Supabaseから取得したキャラクターデータ
    decrement: 減らす量（デフォルト1000）
    """

    user_id_text = row.get("user_id_text")

    # evolution値を減算
    current_value = row.get("evolution", 0)
    new_value = max(current_value - decrement, 0)  # マイナスにならないように保護

    # evolution_countをインクリメント
    current_count = row.get("evolution_count", 0)
    new_count = current_count + 1

    # DB更新
    response = (
        supabase.table("character")
        .update({"evolution": new_value, "evolution_count": new_count})
        .eq("user_id_text", user_id_text)
        .execute()
    )

    return response.data[0] if response.data else None
