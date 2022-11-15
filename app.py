import google_auth_httplib2
import httplib2
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

from dashboard import gastos_category, pago_pngi, deuda_mes


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
        credentials=None,
        adc_cert_path=None,
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
    df["Cargo"] = df["Cargo"].astype(float)
    df["fecha"] = pd.to_datetime(df["fecha de operacion"], format="%Y-%m-%d")

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


# -------------------------

st.set_page_config(page_title="Finanzas", page_icon="🐞", layout="centered")
registros, dashboard = st.tabs(["Registros", "Dashboard"])

with registros:

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
            [[establecimiento, cargo, str(date), etiqueta, tipo_pago, msi]],
        )
        st.success("Gracias! Tu cargo ha sido registrado.")
        st.balloons()

    # expander = st.expander("Ve todos los registros")
    # with expander:
    st.write(f"Open original [Google Sheet]({GSHEET_URL})")
    # st.dataframe(get_data(gsheet_connector))
    AgGrid(get_data(gsheet_connector))

with dashboard:
    st.title("🐞 Dashboard")

    st.subheader("Total gastos del mes y periodo anterior")

    tab = deuda_mes(df=get_data(gsheet_connector), income=117000)
    gpa, gma_no_fijos = st.columns(2)
    gpa.metric(
        "Para no generar intereses (GPNGI)",
        f'{tab.loc["Total GPA", "Monto"]} MXN',
    )
    gma_no_fijos.metric(
        "Gastos No Fijos del mes anterior fuera de GPNGI ",
        f'{tab.loc["Total GMA No Fijos del periodo", "Monto"]} MXN',
    )
    # col2.metric("Wind", "9 mph", "-8%")
    # col3.metric("Humidity", "86%", "4%")

    # expander = st.expander("Ve todos los registros")
    # with expander:
    st.dataframe(deuda_mes(df=get_data(gsheet_connector), income=117000))
