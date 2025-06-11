def validate_product_compliance(product, user_profile):
    return {
        "sebi": product["type"] in ["MF", "Equity"],
        "rbi": not product.get("foreign", False) or user_profile.get("kyc_status") == "verified",
        "irdai": "insurance" not in product["type"].lower() or user_profile.get("insured", False),
        "pfrda": "pension" not in product["type"].lower() or user_profile.get("age", 0) >= 40
    }
