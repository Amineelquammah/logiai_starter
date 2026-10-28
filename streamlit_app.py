"""Interface Streamlit pour tester l'API de prédiction LogiAI."""
import os

import requests
import streamlit as st


st.set_page_config(page_title="LogiAI | Prédiction", page_icon="🚚", layout="centered")
st.title("🚚 LogiAI — Risque de retard")
st.write("Saisissez les informations d'une livraison pour estimer son risque de retard.")

api_url = st.sidebar.text_input(
    "Adresse de l'API",
    value=os.getenv("LOGIAI_API_URL", "http://127.0.0.1:8000"),
    help="Démarrez d'abord l'API FastAPI dans un autre terminal.",
).strip().rstrip("/")

with st.form("delivery_form"):
    st.subheader("Caractéristiques de la livraison")
    left, right = st.columns(2)

    with left:
        distance_km = st.number_input(
            "Distance (km)", min_value=1.0, max_value=1000.0, value=120.0, step=1.0
        )
        poids_kg = st.number_input(
            "Poids (kg)", min_value=0.1, max_value=3000.0, value=450.0, step=1.0
        )
        heure_depart = st.number_input(
            "Heure de départ", min_value=0, max_value=23, value=17, step=1
        )
        type_vehicule = st.selectbox(
            "Type de véhicule", options=["moto", "fourgon", "camion"], index=2
        )

    with right:
        pluie_mm = st.number_input(
            "Pluie prévue (mm)", min_value=0.0, max_value=100.0, value=8.0, step=0.5
        )
        trafic_index = st.number_input(
            "Indice de trafic (0 à 10)",
            min_value=0.0,
            max_value=10.0,
            value=7.5,
            step=0.5,
        )
        nb_arrets = st.number_input(
            "Nombre d'arrêts", min_value=0, max_value=20, value=4, step=1
        )

    submitted = st.form_submit_button("Calculer le risque", type="primary")

if submitted:
    if not api_url:
        st.error("Indiquez l'adresse de l'API dans la barre latérale.")
    else:
        payload = {
            "distance_km": distance_km,
            "poids_kg": poids_kg,
            "heure_depart": heure_depart,
            "pluie_mm": pluie_mm,
            "trafic_index": trafic_index,
            "nb_arrets": nb_arrets,
            "type_vehicule": type_vehicule,
        }

        try:
            response = requests.post(
                f"{api_url}/v1/predict", json=payload, timeout=10
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            try:
                detail = response.json().get("detail", str(error))
            except requests.exceptions.JSONDecodeError:
                detail = response.text or str(error)
            st.error(f"Erreur de l'API ({response.status_code}) : {detail}")
        except requests.ConnectionError:
            st.error(
                "Impossible de joindre l'API. Vérifiez qu'elle est démarrée "
                "et que son adresse est correcte."
            )
        except requests.Timeout:
            st.error("L'API n'a pas répondu dans le délai prévu. Réessayez.")
        except requests.RequestException as error:
            st.error(f"Erreur lors de l'appel à l'API : {error}")
        else:
            try:
                result = response.json()
            except requests.exceptions.JSONDecodeError:
                st.error("L'API a renvoyé une réponse qui n'est pas au format JSON.")
            else:
                probability = result["probabilite_retard"]
                st.subheader("Résultat")
                st.metric("Probabilité de retard", f"{probability:.1%}")
                st.progress(probability, text="Risque estimé")

                if result["alerte"]:
                    st.error("Alerte : cette livraison présente un risque élevé de retard.")
                else:
                    st.success("Pas d'alerte : le risque reste sous le seuil.")

                st.caption(
                    f"Seuil d'alerte : {result['seuil']:.0%} · "
                    f"Version du modèle : {result['model_version']}"
                )
