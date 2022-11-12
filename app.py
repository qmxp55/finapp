import google_auth_httplib2
import httplib2
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest


SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SPREADSHEET_ID = "1smARqiOwAgsFZhNTJAuWPwkJuJ4mwp9tvgClElOFINk"
SHEET_NAME = "records"
GSHEET_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"


@st.experimental_singleton()
def connect_to_gsheet():
    # Create a connection object.
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[SCOPE],
    )

    # Create a new Http() object for every request
    def build_request(http, *args, **kwargs):
        new_http = google_auth_httplib2.AuthorizedHttp(
            credentials, http=httplib2.Http()
        )
        return HttpRequest(new_http, *args, **kwargs)

    authorized_http = google_auth_httplib2.AuthorizedHttp(
        credentials, http=httplib2.Http()
    )
    service = build(
        "sheets",
        "v4",
        requestBuilder=build_request,
        http=authorized_http,
    )
    gsheet_connector = service.spreadsheets()
    return gsheet_connector


def get_data(gsheet_connector) -> pd.DataFrame:
    values = (
        gsheet_connector.values()
        .get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A:F",
        )
        .execute()
    )

    df = pd.DataFrame(values["values"])
    df.columns = df.iloc[0]
    df = df[1:]
    return df


def add_row_to_gsheet(gsheet_connector, row) -> None:
    gsheet_connector.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{SHEET_NAME}!A:F",
        body=dict(values=row),
        valueInputOption="USER_ENTERED",
    ).execute()


def etiquetas():

    et = [
        "Compras Demi",
        "Compras Luz",
        "Compras Omar",
        "Farmacia",
        "Gasolina",
        "Gasto fijo",
        "Otros",
        "Restaurante",
        "Super",
    ]

    return et


def tipo_de_pago():

    return ["B", "BO", "CB", "CI", "DL", "DO", "E", "PL", "PO"]


st.set_page_config(page_title="Finanzas", page_icon="🐞", layout="centered")

st.title("🐞 Registro de gastos")

gsheet_connector = connect_to_gsheet()

st.sidebar.write(
    f"This app shows how a Streamlit app can interact easily with a [Google Sheet]({GSHEET_URL}) to read or store data."
)

st.sidebar.write(
    f"[Read more](https://docs.streamlit.io/knowledge-base/tutorials/databases/public-gsheet) about connecting your Streamlit app to Google Sheets."
)

form = st.form(key="annotation")

with form:
    cols = st.columns((1, 1))
    cargo = cols[0].text_input("Monto:")
    etiqueta = cols[1].selectbox("Etiqueta:", etiquetas(), index=2)
    establecimiento = st.text_input("Establecimiento:")
    date = st.date_input("Fecha de operacion:")
    cols = st.columns((1, 1))
    tipo_pago = cols[0].selectbox("Tipo de pago:", tipo_de_pago(), index=2)
    msi = cols[1].checkbox("MSI")

    submitted = st.form_submit_button(label="Submit")


if submitted:
    add_row_to_gsheet(
        gsheet_connector,
        [[cargo, etiqueta, establecimiento, str(date), tipo_pago, msi]],
    )
    st.success("Gracias! Tucargo ha sido registrado.")
    st.balloons()

expander = st.expander("Ve todos los registros")
with expander:
    st.write(f"Open original [Google Sheet]({GSHEET_URL})")
    st.dataframe(get_data(gsheet_connector))
