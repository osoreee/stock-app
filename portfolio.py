from db import get_client


def list_holdings(user_id: str):
    client = get_client()
    res = (
        client.table("holdings")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at")
        .execute()
    )
    return res.data


def add_holding(user_id: str, symbol: str, name: str, market: str, quantity: float, avg_price: float):
    client = get_client()
    client.table("holdings").insert({
        "user_id": user_id,
        "ticker": symbol,
        "name": name,
        "market": market,
        "quantity": quantity,
        "avg_price": avg_price,
    }).execute()


def delete_holding(holding_id: str):
    client = get_client()
    client.table("holdings").delete().eq("id", holding_id).execute()


def update_holding(holding_id: str, quantity: float, avg_price: float):
    client = get_client()
    client.table("holdings").update({
        "quantity": quantity,
        "avg_price": avg_price,
    }).eq("id", holding_id).execute()
