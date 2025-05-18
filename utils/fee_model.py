"""
Fee calculation based on exchange fee tiers.
"""

# Example fee tier rate mapping; users should replace with actual exchange data
FEE_TIERS = {
    'Tier 0': {'maker': 0.0010, 'taker': 0.0020},
    'Tier 1': {'maker': 0.0008, 'taker': 0.0018},
    'Tier 2': {'maker': 0.0006, 'taker': 0.0016},
}

def calculate_fee(
    price: float,
    quantity: float,
    fee_tier: str,
    is_taker: bool = True
) -> float:
    """
    Calculate order fees for a given price, quantity, and fee tier.

    :param price: execution price in quote currency
    :param quantity: order size in base asset
    :param fee_tier: fee tier key
    :param is_taker: True for taker fee, False for maker fee
    :return: fee amount in quote currency
    """
    tier = FEE_TIERS.get(fee_tier)
    if tier is None:
        raise ValueError(f"Unknown fee tier '{fee_tier}'")
    rate = tier['taker' if is_taker else 'maker']
    return price * quantity * rate