import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"

def api_get(endpoint: str, params=None):
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=20
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        try:
            detail = response.json().get("detail", str(e))
        except Exception:
            detail = str(e)
        st.error(f"Erreur API : {detail}")
    except requests.exceptions.ConnectionError:
        st.error("Impossible de contacter l'API.")
    except requests.exceptions.Timeout:
        st.error("L'API a mis trop de temps à répondre.")
    except Exception as e:
        st.error(f"Erreur inattendue : {e}")
    return None


def get_kpis():
    return api_get("/gold/kpis")


def get_revenue_over_time():
    return api_get("/gold/revenue_over_time")


def get_rfm_distributions():
    return api_get("/gold/rfm/distributions")


def get_customer_segmentation_distributions():
    return api_get("/gold/customer-segmentation/distributions")


def get_customer_segmentation_by_region():
    return api_get("/gold/customer-segmentation/by-region")


def get_customer_segmentation_list(limit=50):
    return api_get("/gold/customer-segmentation/list", params={"limit": limit})


def search_customer(customer_id=None, email_hash=None):
    params = {}

    if customer_id:
        params["customer_id"] = customer_id
    elif email_hash:
        params["email_hash"] = email_hash
    else:
        st.error("Renseigne customer_id ou email_hash.")
        return None

    return api_get("/gold/customer-segmentation/search", params=params)


def list_households(limit=50):
    return api_get("/search/households", params={"limit": limit})


def search_household(household_id):
    return api_get(f"/search/household/{household_id}")