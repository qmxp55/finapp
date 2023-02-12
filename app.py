import google_auth_httplib2
import httplib2
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import HttpRequest
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

from dashboard import gastos_category, pago_pngi, deuda_mes, ingresos, expenses_summary, deuda_tc


SCOPE = "https://www.googleapis.com/auth/spreadsheets"
SPREADSHEET_ID = "1smARqiOwAgsFZhNTJAuWPwkJuJ4mwp9tvgClElOFINk"
# SHEET_NAME = "records"
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


def get_data(gsheet_connector, SHEET_NAME) -> pd.DataFrame:
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
    # print(df)

    if SHEET_NAME == 'records':
        float_cols = ['Cargo']
        date_cols = ['fecha de operacion']
    elif SHEET_NAME == 'resumen_pagos_income':
        float_cols = ['PPNGI', 'Pago efectuado', 'Income']
        date_cols = ['fecha de operacion']
    else:
        raise ValueError(f'{SHEET_NAME} is not a valid Sheet Name.')

    for i in float_cols:
        # df[i].replace('', 0)
        # print(df[i])
        df[i] = df[i].astype(float)
    for i in date_cols:
        df[i] = pd.to_datetime(df[i], format="%Y-%m-%d")

    return df


def add_row_to_gsheet(gsheet_connector, SHEET_NAME, row) -> None:
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

def tipo_de_pago_tc():

    return ["B", "BO", "CB", "CI", "PL", "PO"]

def tipo_de_pago_ed():

    return ["DL", "DO", "E"]

def meses():
    return {'Enero':'1', 'Febrero':'2', 'Marzo':'3', 'Abril':'4', 'Mayo':'5', 'Junio':'6', 'Julio':'7', 'Agosto':'8', 'Septiember':'9', 'Octubre':'10', 'Noviembre':'11', 'Diciembre':'12'}

def years():
    return ['2022', '2023', '2024']

def resumen_deuda_tc(gsheet_connector, month=None, year=None):

    tab_deuda_tc = deuda_tc(df=get_data(gsheet_connector, 'resumen_pagos_income'), month=month, year=year)
    tab_ppngi = pago_pngi(df=get_data(gsheet_connector, 'records'), month=month, year=year)

    tab_ppngi = tab_ppngi.loc[:,'Gastos del periodo anterior (GPA)'].drop(tipo_de_pago_ed() + ['Total'])
    # tab_ppngi['Total'] = sum(tab_ppngi)
    # st.dataframe(tab_ppngi)

    tab_deuda_tc = tab_deuda_tc.set_index('Tarjeta')
    tab_deuda_tc['Deuda mes siguiente'] = tab_deuda_tc['PPNGI'] - tab_deuda_tc['Pago efectuado']
    tab_deuda_tc = tab_ppngi.to_frame().join(tab_deuda_tc)
    tab_deuda_tc.loc['Total']= tab_deuda_tc.sum()

    return tab_deuda_tc

# -------------------------

st.set_page_config(page_title="Finanzas", page_icon="🐞", layout="centered")
registros_gastos, registros_ingresos_pagosTC, dashboard = st.tabs(["Registro de Gastos", "Registro de Ingresos y pagos de TC", "Dashboard"])

with registros_gastos:

    st.title("🐞 Registro de gastos")
    gsheet_connector = connect_to_gsheet()

    # st.sidebar.write(
    #     f"This app shows how a Streamlit app can interact easily with a [Google Sheet]({GSHEET_URL}) to read or store data."
    # )
    # st.sidebar.write(
    #     f"[Read more](https://docs.streamlit.io/knowledge-base/tutorials/databases/public-gsheet) about connecting your Streamlit app to Google Sheets."
    # )

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
            gsheet_connector, 'records',
            [[establecimiento, cargo, str(date), etiqueta, tipo_pago, msi]],
        )
        st.success("Gracias! Tu cargo ha sido registrado.")
        st.balloons()

    # expander = st.expander("Ve todos los registros")
    # with expander:
    st.write(f"Open original [Google Sheet]({GSHEET_URL})")
    # st.dataframe(get_data(gsheet_connector))
    AgGrid(get_data(gsheet_connector, 'records'), fit_columns_on_grid_load=True)

with registros_ingresos_pagosTC:

    st.title("🐞 Registro de Ingresos y Pagos de TC")
    gsheet_connector = connect_to_gsheet()

    # st.sidebar.write(
    #     f"This app shows how a Streamlit app can interact easily with a [Google Sheet]({GSHEET_URL}) to read or store data."
    # )
    # st.sidebar.write(
    #     f"[Read more](https://docs.streamlit.io/knowledge-base/tutorials/databases/public-gsheet) about connecting your Streamlit app to Google Sheets."
    # )

    entry = st.radio(
        "Selecciona el tipo de registro 👉", ('Pago a TC', 'Ingreso E/D'),
    )
    
    form = st.form(key="ingresos-tc")

    with form:
        if entry == 'Pago a TC':
            tipo_pago = st.selectbox("Tipo de pago:", tipo_de_pago_tc(), index=0)
            ppngi = st.text_input("PPNGI:")
            pe = st.text_input("Pago Efectuado:")
            date = st.date_input("Fecha de operacion:")
            income = ''
            
        elif entry == 'Ingreso E/D':
            tipo_pago = st.selectbox("Tipo de pago:", tipo_de_pago_ed(), index=0)
            income = st.text_input("Ingreso:")
            ppngi = ''
            pe = ''
            date = st.date_input("Fecha de operacion:")

        submitted = st.form_submit_button(label="Submit")
        if submitted:
            add_row_to_gsheet(
            gsheet_connector, 'resumen_pagos_income',
            [[tipo_de_pago, ppngi, pe, income, date]],
        )

            st.success("Gracias! Tu Ingreso/Pago TC ha sido registrado.")
            st.balloons()

    # expander = st.expander("Ve todos los registros")
    # with expander:
    st.write(f"Open original [Google Sheet]({GSHEET_URL})")
    # st.dataframe(get_data(gsheet_connector))
    AgGrid(get_data(gsheet_connector, 'resumen_pagos_income'), fit_columns_on_grid_load=True)

with dashboard:

    st.title("🐞 Dashboard")

    current_month = pd.to_datetime("today").strftime("%m")
    cols = st.columns((1,1))
    # mes = cols[0].selectbox("Mes:", list(meses().keys()), index=10)
    mes = cols[0].selectbox("Mes:", list(meses().keys()), index=int(current_month) - 1)
    mes_anterior = cols[0].selectbox("Mes anterior:", list(meses().keys()), index=int(current_month) - 2)
    # print('============>', mes, mes_anterior)
    year = cols[1].selectbox("Año:", years(), index=1)
    income = ingresos(df=get_data(gsheet_connector, 'resumen_pagos_income'), month=meses()[mes], year=year)
    # tab_deuda_tc = deuda_tc(df=get_data(gsheet_connector, 'resumen_pagos_income'), month=meses()[mes], year=year)
    tab_deuda_tc_mes_anterior = resumen_deuda_tc(gsheet_connector, month=meses()[mes_anterior], year=year).round(2)

    st.subheader(f'Resumen pagos a realizar en {mes}')

    tab = deuda_mes(df=get_data(gsheet_connector, 'records'), income=income, month=meses()[mes], year=year)
    with st.container():
        gpa, gma_no_fijos, gmc_fijos, deuda_tc_mes_anterior = st.columns(4)
        # gpa.markdown(f'**GPA/PPNGI**  {tab.loc["Total GPA", "Monto"]} MXN')
        # gpa.markdown(f'#### {tab.loc["Total GPA", "Monto"]} MXN')
        gpa.metric(
            "GPA/PPNGI",
            f'{tab.loc["Total GPA", "Monto"]} MXN',
        )
        gma_no_fijos.metric(
            "GMA No Fijos",
            f'{tab.loc["Total GMA No Fijos del periodo", "Monto"]} MXN',
        )
        gmc_fijos.metric(
            "GMC Fijos D/E",
            f'{tab.loc["Total GMA Fijos del periodo en Debito/efectivo", "Monto"]} MXN',
        )
        deuda_tc_mes_anterior.metric(
            "Deuda PPNGI mes anterior",
            f'{tab_deuda_tc_mes_anterior.loc["Total", "Deuda mes siguiente"]} MXN',
        )

        st.dataframe(resumen_deuda_tc(gsheet_connector, month=meses()[mes], year=year).style.format("{:.2f}"))
        # st.dataframe()

        td, ti, tdisp = st.columns(3)
        td.metric(
            "Total Deuda",
            f'{tab.loc["Total necesario para este mes", "Monto"]} MXN',
        )
        ti.metric(
            "Total E/D Ingresos",
            f'{income} MXN',
        )
        tdisp.metric(
            "Total E/D disponible",
            f'{tab.loc["Disponible para este mes", "Monto"]} MXN',
        )

    # col2.metric("Wind", "9 mph", "-8%")
    # col3.metric("Humidity", "86%", "4%")

    # expander = st.expander("Ve todos los registros")
    # with expander:
    # st.dataframe(deuda_mes(df=get_data(gsheet_connector, 'records'), income=ingresos()))

    st.subheader('Como vamos con los gastos de este mes?')

    df_sum, df_fijo, df_msi = expenses_summary(df=get_data(gsheet_connector, 'records'), month=meses()[mes], year=year)

    gastos_categoria_current = gastos_category(df=get_data(gsheet_connector, 'records'), month=str(int(meses()[mes]) + 1), year=year)
    tab_p = pago_pngi(df=get_data(gsheet_connector, 'records'), month=str(int(meses()[mes]) + 1), year=year)

    # st.dataframe(pago_pngi(df=get_data(gsheet_connector, 'records'), month=str(int(meses()[mes]) + 0), year=year))
    df_sum.loc['Total'] = df_sum.sum()
    st.dataframe(df_sum.style.format("{:.2f}"))
    
    disp_mes = tab.loc['Disponible para este mes', 'Monto']
    disponible_al_dia = disp_mes - tab_p.loc['Total', 'GMA No Fijos']
    # print(f'Disponible al dia: {round(disponible_al_dia, 2)} --> {round(disponible_al_dia * 100 / disp_mes, 2)} %')
    st.metric("Total disponible al dia para Gastos No Fijos", f'{round(disponible_al_dia, 2)} MXN',)

    # gastos por categoria
    st.markdown('#### Gastos No Fijos')
    st.caption('Muestra los gastos no fijos que se deben cubrir este mes.')
    cols = st.columns([1,3])
    gastos_category = gastos_categoria_current.loc['Total', :].drop(["Total", 'Gasto fijo'])
    gastos_category['Total'] = gastos_category.sum()
    gastos_category = gastos_category.round(2)
    cols[0].dataframe(gastos_category.to_frame().style.format("{:.2f}"))
    cols[1].bar_chart(gastos_category.drop('Total'))

    # gastos no fijos
    # cols = st.columns([1,3])
    # cols[0].dataframe(tab_p[['GMA No Fijos']])
    # cols[1].bar_chart(tab_p[['GMA No Fijos']].drop("Total"))

    st.markdown('#### Gastos Fijos')
    st.caption('Muestra los gastos fijos a pagar o que ya se pagaron este mes.')
    st.caption('Incluye gastos fijos del Periodo Anterior para pagos con tarjetas de Credito.')
    st.caption('Y gastos fijos del mes actual para pagos en Efectivo y/o Debito.')
    st.dataframe(df_fijo[['establecimiento', 'Cargo', 'fecha de operacion', 'tipo de pago']])

    st.markdown('#### Gastos a MSI')
    st.caption('Muestra los gastos fijos que estan a Meses Sin Intereses a pagar o que ya se pagaron este mes.')
    st.caption('Incluye gastos fijos del Periodo Anterior para pagos con tarjetas de Credito unicamente.')
    st.dataframe(df_msi)


    # st.markdown('#### Gastos Fijos D/E')
    # st.caption('Muestra los gastos fijos a pagar o que ya se pagaron este mes en efectivo y/o debito.')
    # cols = st.columns([1,3])
    # gpa_fijo_ed = tab_p.loc[:,'GPA Fijos'].drop(tipo_de_pago_tc() + ['Total'])
    # # print(gpa_fijo_ed)
    # gpa_fijo_ed['Total'] = sum(gpa_fijo_ed)
    # cols[0].dataframe(gpa_fijo_ed)
    # cols[1].bar_chart(gpa_fijo_ed.drop("Total"))

    # st.markdown('#### Gastos Fijos Credito')
    # st.caption('Muestra los gastos fijos a pagar el siguiente mes/periodo.')
    # cols = st.columns([1,3])
    # gpa_fijo_tc = tab_p.loc[:,'GPA Fijos'].drop(tipo_de_pago_ed() + ['Total'])
    # gpa_fijo_tc['Total'] = sum(gpa_fijo_tc)
    # cols[0].dataframe(gpa_fijo_tc)
    # cols[1].bar_chart(gpa_fijo_tc.drop("Total"))

    

    # st.subheader('Resumen gastos mes anterior')
    # st.dataframe(pago_pngi(df=get_data(gsheet_connector, 'records'), month=meses()[mes], year=year))
    # st.subheader('Resumen gastos por cateogria mes anterior')
    # st.dataframe(gastos_category(df=get_data(gsheet_connector, 'records'), month=meses()[mes], year=year))

    st.subheader('NOTAS')
    st.markdown('Muestra el total de deuda y el disponible despues de considerar los gastos por tarjeta de credito del periodo anterior y del mes anterior ademas de los gastos fijos en efectivo del mes actual. ')
    st.markdown('**GPA/PPNGI**: Total de Gastos del Periodo Anterior que corresponde al Pago Para No Generar Intereses de todas las tarjetas de credito.')
    st.markdown('**GMA No Fijos**: Total Gastos del Mes Anterior No Fijos. Corresponde a todos los gastos **No Fijos** fuera del GPA pero que se tienen que cubrir con el efectivo/debito disponible de este mes.')
    st.markdown('**GMC Fijos D/E**: Total Gastos del Mes Corriente **Fijos** que se pagan en Efectivo Y Debito.')
    st.markdown('**Total Deuda**: Total necesario para cubrir GPA/PPNGI + GMA No Fijos + GMC Fijos D/E.')
    st.markdown('**Total E/D Ingresos**: Total Ingresos en Efectivo/Debito de este mes.')
    st.markdown('**Total E/D disponible**: Total disponible en Efectivo/Debito de este mes despues de cubrir **Total Deuda**.')
